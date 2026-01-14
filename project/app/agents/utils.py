"""Utility functions for the educational agents."""

import json
import re
from typing import Any

from langchain_openai import ChatOpenAI

from project.config import get_settings


def create_reasoning_llm(
    temperature_override: float | None = None,
    reasoning_effort_override: str | None = None,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance with reasoning metadata support.

    This factory function creates LLM instances configured for OpenAI's
    reasoning models (o1, o3, gpt-5.x). When reasoning is enabled, it
    configures the appropriate reasoning parameters.

    Args:
        temperature_override: Optional temperature to use instead of settings.
            Note: Reasoning models don't support temperature, so this is ignored
            when reasoning is enabled.
        reasoning_effort_override: Optional reasoning effort level to override
            settings. Valid values: "low", "medium", "high".

    Returns:
        Configured ChatOpenAI instance with reasoning support.
    """
    settings = get_settings()

    # Base configuration
    config: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.openai_api_key,
    }

    if settings.reasoning_enabled:
        # Configure reasoning parameters for o1, o3, gpt-5 models
        config["reasoning"] = {
            "effort": reasoning_effort_override or settings.reasoning_effort,
            "summary": settings.reasoning_summary,
        }
        # Use responses/v1 output format for reasoning summaries
        config["output_version"] = "responses/v1"
        # Note: temperature is not supported for reasoning models
    else:
        # Standard model configuration
        config["temperature"] = (
            temperature_override
            if temperature_override is not None
            else settings.llm_temperature
        )

    return ChatOpenAI(**config)


def _normalize_content(content: str | list) -> str:
    """Normalize LLM response content to a string.

    LLM responses can return content as either a string or a list of content blocks
    (especially with OpenAI's reasoning models or newer API versions).

    Args:
        content: The raw content from LLM response (string or list)

    Returns:
        Normalized string content
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Handle list of content blocks (e.g., [{"type": "text", "text": "..."}])
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                # Handle OpenAI-style content blocks
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif "text" in item:
                    text_parts.append(item["text"])
        return "\n".join(text_parts)

    # Fallback: convert to string
    return str(content)


def extract_code_block(content: str | list) -> str:
    """Extract Python code from markdown code blocks.

    Attempts to find code in the following order:
    1. ```python ... ``` blocks
    2. ``` ... ``` blocks (generic)
    3. Returns content as-is if no code block found

    Args:
        content: The LLM response content that may contain code blocks

    Returns:
        The extracted code string, stripped of whitespace
    """
    # Normalize content to string
    content = _normalize_content(content)

    # Try to find ```python ... ``` block
    pattern = r"```python\s*\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to find ``` ... ``` block (generic code block)
    pattern = r"```\s*\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Return content as-is if no code block found
    return content.strip()


def parse_json_response(content: str | list) -> dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks.

    Attempts to extract JSON from:
    1. ```json ... ``` code blocks
    2. ``` ... ``` code blocks
    3. Raw content

    Args:
        content: The LLM response content containing JSON (string or list)

    Returns:
        Parsed JSON as a dictionary, or default structure on failure
    """
    # Normalize content to string
    content = _normalize_content(content)

    # Try to find JSON in ```json ... ``` block
    pattern = r"```json\s*\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        # Try generic code block
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = match.group(1)

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        # Return default structure on parse failure
        return {
            "curriculum": "unknown",
            "intention": "static",
            "concepts": [],
            "summary": content[:200] if content else "Unable to parse response",
        }


def sanitize_manim_code(code: str) -> str:
    """Sanitize Manim code for safe execution.

    Performs basic sanitization to ensure the code is safe to execute:
    - Ensures manim import is present
    - Removes potentially dangerous imports
    - Validates basic structure

    Args:
        code: The Manim Python code to sanitize

    Returns:
        Sanitized code string
    """
    # List of dangerous modules that should not be imported
    dangerous_imports = [
        "subprocess",
        "os.system",
        "eval(",
        "exec(",
        "__import__",
        "importlib",
        "shutil.rmtree",
    ]

    # Check for dangerous patterns
    for pattern in dangerous_imports:
        if pattern in code:
            # Remove lines containing dangerous patterns
            lines = code.split("\n")
            code = "\n".join(
                line for line in lines if pattern not in line
            )

    # Ensure manim import is present
    if "from manim import" not in code and "import manim" not in code:
        code = "from manim import *\n\n" + code

    return code


def extract_scene_name(code: str) -> str | None:
    """Extract the Scene class name from Manim code.

    Args:
        code: The Manim Python code

    Returns:
        The name of the Scene class, or None if not found
    """
    pattern = r"class\s+(\w+)\s*\(\s*Scene\s*\)"
    match = re.search(pattern, code)
    if match:
        return match.group(1)
    return None


class CodeValidationResult:
    """Result of code validation."""

    def __init__(
        self,
        is_valid: bool,
        error_message: str | None = None,
        error_line: int | None = None,
        suggestions: list[str] | None = None,
    ):
        self.is_valid = is_valid
        self.error_message = error_message
        self.error_line = error_line
        self.suggestions = suggestions or []


def validate_manim_code(code: str) -> CodeValidationResult:
    """Validate Manim code for syntax errors and common issues.

    Performs multiple validation checks:
    1. Python syntax validation (compile)
    2. Required imports check
    3. Scene class structure validation
    4. Common Manim API misuse detection

    Args:
        code: The Manim Python code to validate

    Returns:
        CodeValidationResult with validation status and error details
    """
    suggestions = []

    # Check for empty code
    if not code or not code.strip():
        return CodeValidationResult(
            is_valid=False,
            error_message="Code is empty",
            suggestions=["Provide valid Manim code with a Scene class"],
        )

    # Check for manim import
    if "from manim import" not in code and "import manim" not in code:
        suggestions.append("Add 'from manim import *' at the top")

    # Check for Scene class
    scene_name = extract_scene_name(code)
    if not scene_name:
        return CodeValidationResult(
            is_valid=False,
            error_message="No Scene class found in code",
            suggestions=["Create a class that inherits from Scene, e.g., 'class MyScene(Scene):'"],
        )

    # Check for construct method
    if "def construct(self" not in code:
        return CodeValidationResult(
            is_valid=False,
            error_message="No construct method found in Scene class",
            suggestions=["Add 'def construct(self):' method to your Scene class"],
        )

    # Python syntax validation
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        return CodeValidationResult(
            is_valid=False,
            error_message=f"Syntax error: {e.msg}",
            error_line=e.lineno,
            suggestions=[f"Fix syntax error on line {e.lineno}: {e.msg}"],
        )

    # Check for common Manim API misuse patterns
    common_issues = _check_common_manim_issues(code)
    if common_issues:
        return CodeValidationResult(
            is_valid=False,
            error_message=common_issues[0],
            suggestions=common_issues[1:] if len(common_issues) > 1 else [],
        )

    return CodeValidationResult(is_valid=True, suggestions=suggestions)


def _check_common_manim_issues(code: str) -> list[str] | None:
    """Check for common Manim API misuse patterns.

    Args:
        code: The Manim code to check

    Returns:
        List of error message and suggestions, or None if no issues
    """
    issues = []

    # Check for RightAngle with incorrect arguments
    if "RightAngle(" in code:
        # Look for patterns like RightAngle(polygon[0], ...) or RightAngle(triangle[
        if re.search(r"RightAngle\s*\([^)]*\[\d+\]", code):
            issues.append(
                "Incorrect use of RightAngle: RightAngle takes Line objects, not polygon indices"
            )
            issues.append(
                "Use 'Elbow(width=0.3, angle=-PI/2)' or a small Square for right angle markers"
            )
            return issues

    # Check for indexing into Polygon
    if re.search(r"(polygon|triangle)\s*\[\s*\d+\s*\]", code, re.IGNORECASE):
        # Check if it's being used in a problematic context (not just assignment)
        if not re.search(r"=\s*(polygon|triangle)\s*\[", code, re.IGNORECASE):
            issues.append(
                "Potentially incorrect Polygon indexing: Polygon submobjects are not vertices"
            )
            issues.append(
                "Use explicit vertex coordinates [x, y, 0] instead of indexing into polygons"
            )
            return issues

    # Check for np.array without numpy import
    if "np.array(" in code or "np.arctan" in code or "np.cos" in code or "np.sin" in code:
        if "import numpy" not in code and "from numpy" not in code:
            # Check if 'from manim import *' is present (which imports numpy as np)
            if "from manim import *" not in code:
                issues.append("Using numpy functions (np.) without proper import")
                issues.append(
                    "Either add 'import numpy as np' or use 'from manim import *' which includes numpy"
                )
                return issues

    # Check for 2D points instead of 3D
    # Look for patterns like [x, y] without z-coordinate in positioning contexts
    point_pattern = r"(?:move_to|Dot|Line|Arrow|Polygon)\s*\(\s*\[[\d\.\-]+\s*,\s*[\d\.\-]+\s*\]"
    if re.search(point_pattern, code):
        # This is a heuristic check - might have false positives
        pass  # Don't fail on this, just warn

    return None if not issues else issues


def format_error_for_retry(
    code: str,
    error_message: str,
    validation_result: CodeValidationResult | None = None,
) -> str:
    """Format error information for retry prompt.

    Creates a detailed error description that can be used to help
    the LLM fix the code.

    Args:
        code: The original code that failed
        error_message: The error message from execution or validation
        validation_result: Optional validation result with suggestions

    Returns:
        Formatted error string for the retry prompt
    """
    parts = [
        "## Error Details",
        "",
        f"**Error Message:** {error_message}",
        "",
    ]

    if validation_result:
        if validation_result.error_line:
            parts.append(f"**Error Line:** {validation_result.error_line}")
            parts.append("")

        if validation_result.suggestions:
            parts.append("**Suggestions:**")
            for suggestion in validation_result.suggestions:
                parts.append(f"- {suggestion}")
            parts.append("")

    # Add the problematic code with line numbers
    parts.append("## Code That Failed")
    parts.append("")
    parts.append("```python")
    for i, line in enumerate(code.split("\n"), 1):
        parts.append(f"{i:3}: {line}")
    parts.append("```")

    return "\n".join(parts)
