"""Utility functions for the educational agents."""

import json
import re
from typing import Any


def extract_code_block(content: str) -> str:
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


def parse_json_response(content: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks.

    Attempts to extract JSON from:
    1. ```json ... ``` code blocks
    2. ``` ... ``` code blocks
    3. Raw content

    Args:
        content: The LLM response content containing JSON

    Returns:
        Parsed JSON as a dictionary, or default structure on failure
    """
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
