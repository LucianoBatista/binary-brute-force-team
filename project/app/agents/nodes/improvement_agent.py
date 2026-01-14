"""Improvement Agent node for the educational workflow.

This node improves existing Manim code based on user feedback.
"""

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import (
    create_reasoning_llm,
    extract_code_block,
    sanitize_manim_code,
)
from project.app.schemas.educational import EducationalState


async def improvement_agent(state: EducationalState) -> EducationalState:
    """Improve existing Manim code based on user feedback.

    This node uses an LLM to analyze and improve Manim code according
    to the user's specific requests.

    Args:
        state: The current workflow state with existing manim_code and feedback

    Returns:
        Updated state with improved manim_code and code_explanation
    """
    # Use medium reasoning effort for precise improvements
    llm = create_reasoning_llm(reasoning_effort_override="medium")

    # Format the detected concepts as a string
    concepts_str = ", ".join(state["detected_concepts"]) if state["detected_concepts"] else "general concepts"

    # Get existing code or use a placeholder
    existing_code = state.get("manim_code", "")
    if not existing_code:
        existing_code = "# No existing code provided"

    # Render the prompt with context
    prompt = render_prompt(
        "improvement_agent",
        manim_code=existing_code,
        user_query=state["user_query"],
        curriculum_component=state["curriculum_component"],
        detected_concepts=concepts_str,
    )

    # Get LLM response
    response = await llm.ainvoke(prompt)

    # Extract code from the response
    code = extract_code_block(response.content)

    # Sanitize the code for safe execution
    code = sanitize_manim_code(code)

    return {
        **state,
        "manim_code": code,
        "code_explanation": "Code improved based on user feedback",
    }
