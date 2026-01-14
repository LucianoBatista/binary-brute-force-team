"""Dynamic Generator node for the educational workflow.

This node generates Manim code for dynamic animations that explain
educational concepts step by step.
"""

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import (
    create_reasoning_llm,
    extract_code_block,
    sanitize_manim_code,
)
from project.app.schemas.educational import EducationalState


async def dynamic_generator(state: EducationalState) -> EducationalState:
    """Generate dynamic Manim animation code.

    This node uses an LLM to generate Manim code that creates animated
    educational content with step-by-step explanations.

    Args:
        state: The current workflow state with detected concepts and content

    Returns:
        Updated state with manim_code and code_explanation
    """
    # Use medium reasoning effort for creative code generation
    llm = create_reasoning_llm(reasoning_effort_override="medium")

    # Format the detected concepts as a string
    concepts_str = (
        ", ".join(state["detected_concepts"])
        if state["detected_concepts"]
        else "general concepts"
    )

    # Render the prompt with context
    prompt = render_prompt(
        "dynamic_generator",
        curriculum_component=state["curriculum_component"],
        detected_concepts=concepts_str,
        analysis_summary=state["analysis_summary"],
        pdf_text=state["pdf_text"],
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
        "code_explanation": f"Dynamic animation generated for {state['curriculum_component']} content",
    }
