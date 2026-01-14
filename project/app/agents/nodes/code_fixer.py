"""Code Fixer node for the educational workflow.

This node attempts to fix broken Manim code by analyzing the error
and regenerating corrected code using an LLM.
"""

import logging

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import (
    CodeValidationResult,
    create_reasoning_llm,
    extract_code_block,
    format_error_for_retry,
    sanitize_manim_code,
    validate_manim_code,
)
from project.app.schemas.educational import EducationalState

logger = logging.getLogger(__name__)


async def code_fixer(state: EducationalState) -> EducationalState:
    """Fix broken Manim code based on error feedback.

    This node takes failed Manim code and the error message, then uses
    an LLM to generate corrected code.

    Args:
        state: The current workflow state with manim_code and error_message

    Returns:
        Updated state with fixed manim_code and reset error state
    """
    current_retries = state.get("retry_count", 0)
    logger.info(
        "Code fixer starting - Retry attempt %d. Attempting to fix Manim code...",
        current_retries + 1,
    )

    # Use high reasoning effort for precise code fixes
    llm = create_reasoning_llm(reasoning_effort_override="high")

    # Get the current code and error
    failed_code = state.get("manim_code", "")
    error_message = state.get("error_message", "Unknown error")

    logger.debug("Error to fix: %s", error_message)

    # Validate and get detailed error info
    validation_result = validate_manim_code(failed_code)

    # Format error details for the prompt
    error_details = format_error_for_retry(
        code=failed_code,
        error_message=error_message,
        validation_result=validation_result if not validation_result.is_valid else None,
    )

    # Format the detected concepts as a string
    concepts_str = (
        ", ".join(state["detected_concepts"])
        if state.get("detected_concepts")
        else "general concepts"
    )

    # Render the code fixer prompt
    prompt = render_prompt(
        "code_fixer",
        manim_code=failed_code,
        error_details=error_details,
        curriculum_component=state.get("curriculum_component", "unknown"),
        detected_concepts=concepts_str,
        user_query=state.get("user_query", ""),
    )

    # Get LLM response
    response = await llm.ainvoke(prompt)

    # Extract and sanitize the fixed code
    fixed_code = extract_code_block(response.content)
    fixed_code = sanitize_manim_code(fixed_code)

    logger.info(
        "Code fixer completed - Retry attempt %d. Fixed code generated, routing back to media_generator.",
        current_retries + 1,
    )

    return {
        **state,
        "manim_code": fixed_code,
        "error_message": None,  # Clear the error for retry
        "execution_status": "pending",  # Reset status for retry
        "retry_count": current_retries + 1,
    }
