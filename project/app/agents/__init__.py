"""Agents package for the educational content generation system.

This package contains LangGraph workflows and agent nodes for generating
educational content with Manim visualizations.
"""

from project.app.agents.educational_workflow import (
    create_educational_workflow,
    educational_graph,
    run_educational_workflow,
)
from project.app.agents.nodes import (
    dynamic_generator,
    improvement_agent,
    intention_detector,
    media_generator,
    static_generator,
)
from project.app.agents.prompt_loader import (
    clear_prompt_cache,
    list_available_prompts,
    load_prompt,
    render_prompt,
)
from project.app.agents.tools import ToolRegistry, tool_registry
from project.app.agents.utils import (
    extract_code_block,
    extract_scene_name,
    parse_json_response,
    sanitize_manim_code,
)

__all__ = [
    # Workflow
    "create_educational_workflow",
    "educational_graph",
    "run_educational_workflow",
    # Nodes
    "intention_detector",
    "static_generator",
    "dynamic_generator",
    "improvement_agent",
    "media_generator",
    # Prompt utilities
    "load_prompt",
    "render_prompt",
    "clear_prompt_cache",
    "list_available_prompts",
    # Tools
    "ToolRegistry",
    "tool_registry",
    # Utilities
    "extract_code_block",
    "parse_json_response",
    "sanitize_manim_code",
    "extract_scene_name",
]
