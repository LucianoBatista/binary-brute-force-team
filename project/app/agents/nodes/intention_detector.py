"""Intention Detector node for the educational workflow.

This node analyzes the input content to detect:
- Curriculum component (math, chemistry, physics)
- User intention (static, dynamic, improvement)
- Key educational concepts
"""

from langchain_openai import ChatOpenAI

from project.app.agents.prompt_loader import render_prompt
from project.app.agents.utils import parse_json_response
from project.app.schemas.educational import EducationalState
from project.config import Settings

settings = Settings()


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
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.0,  # Use low temperature for consistent classification
        api_key=settings.openai_api_key,
    )

    # Render the prompt with the input data
    prompt = render_prompt(
        "intention_detector",
        pdf_text=state["pdf_text"],
        user_query=state["user_query"],
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
