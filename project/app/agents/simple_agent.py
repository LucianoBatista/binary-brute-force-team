from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from project.config import get_settings


class AgentState(TypedDict):
    """State definition for the multi-agent workflow"""

    query: str
    analysis: str
    result: str


async def run_simple_agent(query: str) -> dict:
    """
    Simple multi-agent workflow demonstrating LangGraph capabilities.

    Workflow:
    1. Analyzer agent: Understands and breaks down the query
    2. Executor agent: Processes the query and generates a response

    Args:
        query: User's input query

    Returns:
        Dict with text response and optional media:
        {
            "text": str,           # Text response
            "media_url": str,      # Optional URL to image/video
            "media_type": str      # Optional MIME type
        }
    """
    settings = get_settings()

    # Initialize LLM
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key,
    )

    # Define agent nodes
    def analyzer(state: AgentState) -> AgentState:
        """Analyzer agent: Breaks down the query"""
        prompt = f"Analyze this query and identify key concepts: {state['query']}"
        response = llm.invoke(prompt)
        return {**state, "analysis": response.content}

    def executor(state: AgentState) -> AgentState:
        """Executor agent: Generates the final response"""
        prompt = f"""Based on the following analysis, provide a clear and educational response.

Analysis: {state["analysis"]}
Original Query: {state["query"]}

Provide a detailed, accurate response suitable for STEM education."""
        response = llm.invoke(prompt)
        return {**state, "result": response.content}

    # Build the workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyzer", analyzer)
    workflow.add_node("executor", executor)

    # Define edges
    workflow.add_edge("analyzer", "executor")
    workflow.add_edge("executor", END)

    # Set entry point
    workflow.set_entry_point("analyzer")

    # Compile and execute
    graph = workflow.compile()
    final_state = await graph.ainvoke({"query": query, "analysis": "", "result": ""})

    # Return structured response with optional media
    # TODO: Add image/video generation logic here
    # For now, returning text-only response
    return {
        "text": final_state["result"],
        "media_url": None,
        "media_type": None
    }
