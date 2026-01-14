"""Intention Detector node for the educational workflow.

This node analyzes the input content to detect:
- Curriculum component (math, chemistry, physics)
- User intention (static, dynamic, improvement)
- Key educational concepts
"""

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import create_reasoning_llm, parse_json_response
from project.app.schemas.educational import EducationalState


async def intention_detector(state: EducationalState) -> EducationalState:
    """Detect curriculum component and user intention.

    This node uses an LLM to analyze the PDF content and user query to
    determine what type of educational content should be generated.

    Args:
        state: The current workflow state containing pdf_text and user_query

    Returns:
        Updated state with curriculum_component, intention_type,
        detected_concepts, and analysis_summary
    """
    # Use low reasoning effort for consistent classification
    llm = create_reasoning_llm(reasoning_effort_override="low")

    existing_code = state.get("manim_code")
    if not existing_code:
        existing_code = "# No existing code provided"

    user_query = state.get("user_query")
    if not user_query:
        user_query = "There is no user query"

    # Render the prompt with the input data
    prompt = render_prompt(
        "intention_detector",
        pdf_text=state["pdf_text"],
        user_query=user_query,
        manim_code=existing_code,
    )

    # Get LLM response
    response = await llm.ainvoke(prompt)

    # Parse the JSON response
    parsed = parse_json_response(response.content)

    # Validate and normalize the curriculum component
    curriculum = parsed.get("curriculum", "unknown")
    if curriculum not in ("math", "chemistry", "physics", "unknown"):
        curriculum = "unknown"

    # Validate and normalize the intention type
    intention = parsed.get("intention", "static")
    if intention not in ("static", "dynamic", "improvement"):
        intention = "static"

    # Extract concepts (ensure it's a list)
    concepts = parsed.get("concepts", [])
    if not isinstance(concepts, list):
        concepts = []

    # Get the summary
    summary = parsed.get("summary", "")

    return {
        **state,
        "curriculum_component": curriculum,
        "intention_type": intention,
        "detected_concepts": concepts,
        "analysis_summary": summary,
    }
