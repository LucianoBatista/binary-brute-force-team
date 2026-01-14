"""Educational content generation workflow using LangGraph.

This module defines the main multi-agent workflow for generating
educational content with Manim visualizations.

Flow:
    PDF Input → Intention Detector → Content Generator → Media Generator

The Content Generator is dynamically selected based on the detected intention:
- Static Generator: For static visualizations/diagrams
- Dynamic Generator: For animated explanations
- Improvement Agent: For improving existing Manim code
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from project.app.agents.nodes import (
    dynamic_generator,
    improvement_agent,
    intention_detector,
    media_generator,
    static_generator,
)
from project.app.schemas.educational import EducationalState


def route_by_intention(state: EducationalState) -> str:
    """Route to appropriate content generator based on detected intention.

    Args:
        state: The current workflow state with intention_type

    Returns:
        The name of the next node to execute
    """
    intention = state.get("intention_type", "static")

    routing_map = {
        "static": "static_generator",
        "dynamic": "dynamic_generator",
        "improvement": "improvement_agent",
    }

    return routing_map.get(intention, "static_generator")


def create_educational_workflow() -> StateGraph:
    """Create the multi-agent educational workflow graph.

    The workflow follows this structure:
    1. intention_detector: Analyzes input to determine content type
    2. Conditional routing to one of:
       - static_generator: Creates static visualizations
       - dynamic_generator: Creates animations
       - improvement_agent: Improves existing code
    3. media_generator: Executes Manim and produces output

    Returns:
        Compiled LangGraph workflow
    """
    # Create the state graph
    workflow = StateGraph(EducationalState)

    # Add nodes
    workflow.add_node("intention_detector", intention_detector)
    workflow.add_node("static_generator", static_generator)
    workflow.add_node("dynamic_generator", dynamic_generator)
    workflow.add_node("improvement_agent", improvement_agent)
    workflow.add_node("media_generator", media_generator)

    # Set entry point
    workflow.set_entry_point("intention_detector")

    # Add conditional routing after intention detection
    workflow.add_conditional_edges(
        "intention_detector",
        route_by_intention,
        {
            "static_generator": "static_generator",
            "dynamic_generator": "dynamic_generator",
            "improvement_agent": "improvement_agent",
        },
    )

    # All content generators lead to media generator
    workflow.add_edge("static_generator", "media_generator")
    workflow.add_edge("dynamic_generator", "media_generator")
    workflow.add_edge("improvement_agent", "media_generator")

    # Media generator ends the workflow
    workflow.add_edge("media_generator", END)

    # Compile with in-memory checkpointing
    # For production, consider using SqliteSaver or PostgresSaver
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Create singleton graph instance
educational_graph = create_educational_workflow()


async def run_educational_workflow(
    pdf_text: str,
    user_query: str,
    thread_id: str = "default",
    existing_code: str | None = None,
) -> dict:
    """Execute the educational content workflow.

    Args:
        pdf_text: The extracted text from the PDF document
        user_query: The user's query/request for content generation
        thread_id: Unique identifier for the conversation thread
        existing_code: Optional existing Manim code (for improvement workflow)

    Returns:
        Dictionary with workflow results including:
        - media_path: Path to generated media
        - media_type: MIME type of the media
        - status: Execution status (success/failed)
        - error: Error message if failed
        - curriculum: Detected curriculum component
        - intention: Detected intention type
        - manim_code: The generated Manim code
    """
    # Initialize the state
    initial_state: EducationalState = {
        "pdf_text": pdf_text,
        "user_query": user_query,
        "curriculum_component": "unknown",
        "intention_type": "static",
        "detected_concepts": [],
        "analysis_summary": "",
        "manim_code": existing_code or "",
        "code_explanation": "",
        "media_path": None,
        "media_type": None,
        "execution_status": "pending",
        "error_message": None,
    }

    # Configure the execution with thread_id for checkpointing
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the workflow
    result = await educational_graph.ainvoke(initial_state, config=config)

    # Return a clean response dictionary
    return {
        "media_path": result.get("media_path"),
        "media_type": result.get("media_type"),
        "status": result.get("execution_status"),
        "error": result.get("error_message"),
        "curriculum": result.get("curriculum_component"),
        "intention": result.get("intention_type"),
        "manim_code": result.get("manim_code"),
        "detected_concepts": result.get("detected_concepts", []),
        "analysis_summary": result.get("analysis_summary", ""),
    }
