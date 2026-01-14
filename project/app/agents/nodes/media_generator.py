"""Media Generator node for the educational workflow.

This node executes Manim code and generates media output (video/image).
It includes pre-execution validation to catch common errors before running Manim.
"""

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from project.app.agents.utils import extract_scene_name, validate_manim_code
from project.app.schemas.educational import EducationalState

# Output directory for generated media
MEDIA_OUTPUT_DIR = Path("project/app/static/generated")


def ensure_output_dir() -> None:
    """Ensure the output directory exists."""
    MEDIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_generated_media(temp_dir: str, scene_name: str | None) -> Path | None:
    """Find the generated media file in Manim's output directory.

    Args:
        temp_dir: The temporary directory where Manim was executed
        scene_name: The name of the Scene class

    Returns:
        Path to the generated media file, or None if not found
    """
    # Manim generates media in a 'media' subdirectory
    media_dir = Path(temp_dir) / "media" / "videos"

    if not media_dir.exists():
        return None

    # Search for video files (mp4)
    for video_file in media_dir.rglob("*.mp4"):
        return video_file

    # Search for image files (png) if no video found
    images_dir = Path(temp_dir) / "media" / "images"
    if images_dir.exists():
        for image_file in images_dir.rglob("*.png"):
            return image_file

    return None


async def media_generator(state: EducationalState) -> EducationalState:
    """Execute Manim code and generate media.

    This node takes the generated Manim code, validates it, executes it
    using subprocess, and saves the output media to the static directory.

    The node includes pre-execution validation to catch common errors
    before running Manim, providing detailed error messages for the
    code fixer to use in retry attempts.

    Args:
        state: The current workflow state with manim_code

    Returns:
        Updated state with media_path, media_type, and execution_status
    """
    ensure_output_dir()

    # Preserve retry count
    retry_count = state.get("retry_count", 0)

    # Check if there's code to execute
    if not state.get("manim_code"):
        return {
            **state,
            "execution_status": "failed",
            "error_message": "No Manim code to execute",
            "retry_count": retry_count,
        }

    # Validate code before execution
    validation_result = validate_manim_code(state["manim_code"])
    if not validation_result.is_valid:
        error_msg = validation_result.error_message or "Code validation failed"
        if validation_result.suggestions:
            error_msg += f". Suggestions: {'; '.join(validation_result.suggestions)}"
        return {
            **state,
            "execution_status": "failed",
            "error_message": error_msg,
            "retry_count": retry_count,
        }

    # Extract scene name from the code
    scene_name = extract_scene_name(state["manim_code"])
    if not scene_name:
        return {
            **state,
            "execution_status": "failed",
            "error_message": "Could not find Scene class in the code",
            "retry_count": retry_count,
        }

    # Create a temporary directory for execution
    temp_dir = tempfile.mkdtemp(prefix="manim_")

    try:
        # Write the Manim code to a temporary file
        code_file = Path(temp_dir) / "scene.py"
        code_file.write_text(state["manim_code"])

        # Execute Manim
        result = subprocess.run(
            [
                "manim",
                "-qm",  # Medium quality
                "--media_dir",
                str(Path(temp_dir) / "media"),
                str(code_file),
                scene_name,
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=temp_dir,
            env={**os.environ, "PYTHONPATH": str(Path.cwd())},
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown Manim error"
            # Capture more of the error for better debugging
            return {
                **state,
                "execution_status": "failed",
                "error_message": f"Manim execution failed: {error_msg[:1000]}",
                "retry_count": retry_count,
            }

        # Find the generated media file
        generated_file = find_generated_media(temp_dir, scene_name)

        if not generated_file:
            return {
                **state,
                "execution_status": "failed",
                "error_message": "Manim ran successfully but no output file was found",
                "retry_count": retry_count,
            }

        # Generate a unique filename and copy to output directory
        file_id = str(uuid.uuid4())[:8]
        extension = generated_file.suffix
        output_filename = f"{scene_name}_{file_id}{extension}"
        output_path = MEDIA_OUTPUT_DIR / output_filename

        shutil.copy2(generated_file, output_path)

        # Determine media type
        media_type = "video/mp4" if extension == ".mp4" else "image/png"

        # Return the relative URL path for serving
        relative_path = f"/static/generated/{output_filename}"

        return {
            **state,
            "media_path": relative_path,
            "media_type": media_type,
            "execution_status": "success",
            "error_message": None,
            "retry_count": retry_count,
        }

    except subprocess.TimeoutExpired:
        return {
            **state,
            "execution_status": "failed",
            "error_message": "Manim execution timed out (120s limit)",
            "retry_count": retry_count,
        }
    except Exception as e:
        return {
            **state,
            "execution_status": "failed",
            "error_message": f"Error during media generation: {str(e)}",
            "retry_count": retry_count,
        }
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
