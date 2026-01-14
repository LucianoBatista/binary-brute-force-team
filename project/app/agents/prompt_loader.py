"""Prompt loader utility for loading and rendering markdown prompts."""

from functools import lru_cache
from pathlib import Path

# Path to the prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@lru_cache(maxsize=20)
def load_prompt(name: str) -> str:
    """Load a markdown prompt file with caching.

    The prompt files are loaded from the project/app/prompts/ directory.
    Results are cached to avoid repeated file I/O.

    Args:
        name: The name of the prompt file (without .md extension)

    Returns:
        The content of the prompt file as a string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **variables: str) -> str:
    """Load and render a prompt template with variables.

    Uses Python's str.format() for variable substitution.
    Variables in the template should be in {variable_name} format.

    Args:
        name: The name of the prompt file (without .md extension)
        **variables: Keyword arguments to substitute in the template

    Returns:
        The rendered prompt string with variables substituted

    Example:
        >>> prompt = render_prompt(
        ...     "intention_detector",
        ...     pdf_text="Some educational content",
        ...     user_query="Create a visualization"
        ... )
    """
    template = load_prompt(name)
    return template.format(**variables)


def clear_prompt_cache() -> None:
    """Clear the prompt cache.

    Useful for development when prompt files are being edited.
    """
    load_prompt.cache_clear()


def list_available_prompts() -> list[str]:
    """List all available prompt templates.

    Returns:
        A list of prompt names (without .md extension)
    """
    if not PROMPTS_DIR.exists():
        return []
    return [p.stem for p in PROMPTS_DIR.glob("*.md")]
