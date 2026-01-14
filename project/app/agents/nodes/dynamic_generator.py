"""Dynamic Generator node for the educational workflow.

This node generates Manim code for dynamic animations that explain
educational concepts step by step.
"""

from langchain_openai import ChatOpenAI

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import extract_code_block, sanitize_manim_code
from project.app.schemas.educational import EducationalState
from project.config import Settings

settings = Settings()


async def dynamic_generator(state: EducationalState) -> EducationalState:
    """Generate dynamic Manim animation code.

    This node uses an LLM to generate Manim code that creates animated
    educational content with step-by-step explanations.

    Args:
        state: The current workflow state with detected concepts and content

    Returns:
        Updated state with manim_code and code_explanation
    """
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.3,  # Slightly higher temperature for creative animation
        api_key=settings.openai_api_key,
    )

    # Format the detected concepts as a string
    concepts_str = ", ".join(state["detected_concepts"]) if state["detected_concepts"] else "general concepts"

    # Render the prompt with context
    prompt = render_prompt(
        "dynamic_generator",
        curriculum_component=state["curriculum_component"],
        detected_concepts=concepts_str,
        analysis_summary=state["analysis_summary"],
        pdf_text=state["pdf_text"],
        user_query=state["user_query"],
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
