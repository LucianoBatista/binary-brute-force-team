#!/usr/bin/env -S uv run
"""Validation script for the educational multi-agent workflow.

This script reads PDF text from a markdown file and runs the educational
workflow to generate Manim visualizations, saving outputs and logs for
validation before route integration.

Usage:
    uv run scripts/validate_educational_workflow.py \
        --input scripts/input/sample.md \
        --query "Create a visualization of the Pythagorean theorem"
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from project.app.agents.educational_workflow import run_educational_workflow


def setup_logging(output_dir: Path, verbose: bool = False) -> logging.Logger:
    """Configure logging with console and file handlers.

    Args:
        output_dir: Directory for log files
        verbose: Enable debug-level logging

    Returns:
        Configured logger instance
    """
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"workflow_{timestamp}.log"

    logger = logging.getLogger("educational_workflow")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (always verbose)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content.

    Supports simple key: value pairs in frontmatter.

    Args:
        content: Raw markdown content

    Returns:
        Tuple of (frontmatter dict, remaining content)
    """
    frontmatter = {}
    remaining = content

    # Check for frontmatter delimiters
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            remaining = parts[2].strip()

            # Parse simple key: value pairs
            for line in frontmatter_text.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    frontmatter[key] = value

    return frontmatter, remaining


def read_markdown_file(file_path: Path) -> tuple[str, str | None]:
    """Read markdown file and extract PDF text and optional query.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (pdf_text, query or None)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    frontmatter, pdf_text = parse_frontmatter(content)

    query = frontmatter.get("query")

    return pdf_text, query


def copy_generated_media(
    media_path: str | None,
    output_dir: Path,
    logger: logging.Logger,
) -> Path | None:
    """Copy generated media from project static directory to output.

    Args:
        media_path: Relative path from workflow result (e.g., /static/generated/...)
        output_dir: Target output directory
        logger: Logger instance

    Returns:
        Path to copied file or None if no media
    """
    if not media_path:
        logger.warning("No media path in workflow result")
        return None

    # Construct source path - media_path is relative like /static/generated/...
    # The actual file is in project/app/static/generated/
    if media_path.startswith("/static/"):
        relative_path = media_path[8:]  # Remove "/static/"
        source_path = PROJECT_ROOT / "project" / "app" / "static" / relative_path
    else:
        source_path = Path(media_path)

    if not source_path.exists():
        logger.error(f"Generated media not found at: {source_path}")
        return None

    # Copy to output
    media_dir = output_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    dest_path = media_dir / source_path.name

    shutil.copy2(source_path, dest_path)
    logger.info(f"Media copied to: {dest_path}")

    return dest_path


def save_results(
    result: dict,
    output_dir: Path,
    logger: logging.Logger,
) -> None:
    """Save workflow results to output directory.

    Args:
        result: Workflow result dictionary
        output_dir: Target output directory
        logger: Logger instance
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save full result as JSON
    result_file = output_dir / "result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to: {result_file}")

    # Save Manim code separately if available
    if result.get("manim_code"):
        code_file = output_dir / "manim_code.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(result["manim_code"])
        logger.info(f"Manim code saved to: {code_file}")


def print_summary(result: dict, media_dest: Path | None) -> None:
    """Print a summary of the workflow execution.

    Args:
        result: Workflow result dictionary
        media_dest: Path to copied media file
    """
    print("\n" + "=" * 60)
    print("WORKFLOW EXECUTION SUMMARY")
    print("=" * 60)

    print(f"\nStatus: {result.get('status', 'unknown')}")
    print(f"Curriculum: {result.get('curriculum', 'unknown')}")
    print(f"Intention: {result.get('intention', 'unknown')}")

    concepts = result.get("detected_concepts", [])
    if concepts:
        print(f"Detected Concepts: {', '.join(concepts)}")

    summary = result.get("analysis_summary", "")
    if summary:
        print(
            f"\nAnalysis Summary:\n{summary[:500]}{'...' if len(summary) > 500 else ''}"
        )

    if result.get("error"):
        print(f"\nError: {result['error']}")

    if media_dest:
        print(f"\nGenerated Media: {media_dest}")

    if result.get("manim_code"):
        code_lines = len(result["manim_code"].split("\n"))
        print(f"Manim Code: {code_lines} lines")

    print("\n" + "=" * 60)


async def run_workflow(
    pdf_text: str,
    query: str,
    thread_id: str,
    existing_code: str | None,
    logger: logging.Logger,
) -> dict:
    """Execute the educational workflow with logging.

    Args:
        pdf_text: PDF content text
        query: User query for content generation
        thread_id: Thread ID for checkpointing
        existing_code: Optional existing Manim code
        logger: Logger instance

    Returns:
        Workflow result dictionary
    """
    logger.info("Starting educational workflow...")
    logger.debug(f"PDF text length: {len(pdf_text)} characters")
    logger.debug(f"Query: {query}")
    logger.debug(f"Thread ID: {thread_id}")

    if existing_code:
        logger.debug(f"Existing code provided: {len(existing_code)} characters")

    try:
        result = await run_educational_workflow(
            pdf_text=pdf_text,
            user_query=query,
            thread_id=thread_id,
            existing_code=existing_code,
        )

        logger.info(f"Workflow completed with status: {result.get('status')}")
        logger.debug(f"Curriculum: {result.get('curriculum')}")
        logger.debug(f"Intention: {result.get('intention')}")
        logger.debug(f"Detected concepts: {result.get('detected_concepts')}")

        if result.get("error"):
            logger.error(f"Workflow error: {result['error']}")

        return result

    except Exception as e:
        logger.exception(f"Workflow execution failed: {e}")
        raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate the educational multi-agent workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  uv run scripts/validate_educational_workflow.py \\
    --input scripts/input/sample.md \\
    --query "Create a visualization of the Pythagorean theorem"

  # With verbose logging
  uv run scripts/validate_educational_workflow.py \\
    --input scripts/input/sample.md \\
    --query "Create an animated explanation" \\
    --verbose

  # Use query from markdown frontmatter
  uv run scripts/validate_educational_workflow.py \\
    --input scripts/input/sample.md \\
    --verbose
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to markdown file containing PDF text",
    )

    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="User query for content generation (overrides frontmatter query)",
    )

    parser.add_argument(
        "--thread-id",
        "-t",
        type=str,
        default=None,
        help="Thread ID for checkpointing (default: auto-generated)",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path(__file__).parent / "output",
        help="Output directory for results (default: scripts/output)",
    )

    parser.add_argument(
        "--existing-code",
        "-e",
        type=Path,
        help="Path to existing Manim code file (for improvement workflow)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Setup output directory
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(output_dir, args.verbose)

    try:
        # Read input markdown
        logger.info(f"Reading input file: {args.input}")
        pdf_text, frontmatter_query = read_markdown_file(args.input)

        # Determine query (CLI overrides frontmatter)
        query = args.query or frontmatter_query
        if not query:
            logger.error(
                "No query provided. Use --query or add 'query:' to frontmatter"
            )
            return 1

        # Generate thread ID if not provided
        thread_id = (
            args.thread_id or f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Read existing code if provided
        existing_code = None
        if args.existing_code:
            if args.existing_code.exists():
                existing_code = args.existing_code.read_text(encoding="utf-8")
                logger.info(f"Loaded existing code from: {args.existing_code}")
            else:
                logger.warning(f"Existing code file not found: {args.existing_code}")

        # Run the workflow
        result = asyncio.run(
            run_workflow(
                pdf_text=pdf_text,
                query=query,
                thread_id=thread_id,
                existing_code=existing_code,
                logger=logger,
            )
        )

        # Copy generated media
        media_dest = copy_generated_media(result.get("media_path"), output_dir, logger)

        # Save results
        save_results(result, output_dir, logger)

        # Print summary
        print_summary(result, media_dest)

        # Return based on status
        if result.get("status") == "success":
            logger.info("Workflow validation completed successfully")
            return 0
        else:
            logger.warning("Workflow completed with non-success status")
            return 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
