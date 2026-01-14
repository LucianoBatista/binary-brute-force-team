"""Static Generator node for the educational workflow.

This node generates Manim code for static visualizations (images/diagrams)
based on the educational content.
"""

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import (
    create_reasoning_llm,
    extract_code_block,
    sanitize_manim_code,
)
from project.app.schemas.educational import EducationalState


async def static_generator(state: EducationalState) -> EducationalState:
    """Generate static Manim visualization code.

    This node uses an LLM to generate Manim code that creates static
    educational visualizations like diagrams and illustrations.

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
        "static_generator",
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
        "code_explanation": f"Static visualization generated for {state['curriculum_component']} content",
    }
