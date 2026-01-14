"""API router for the educational content generation workflow.

This module provides FastAPI endpoints for generating educational content
with Manim visualizations.
"""

import uuid

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import HTMLResponse

from project.app.agents.educational_workflow import run_educational_workflow
from project.app.schemas.educational import (
    EducationalWorkflowRequest,
    EducationalWorkflowResponse,
)

router = APIRouter(prefix="/api/educational", tags=["Educational"])


@router.post("/generate", response_class=HTMLResponse)
async def generate_content(request: EducationalWorkflowRequest = Body(...)) -> str:
    """Generate educational content from PDF text.

    This endpoint executes the full educational workflow:
    1. Detects the curriculum component and user intention
    2. Generates appropriate Manim code
    3. Executes Manim to produce media

    Returns HTML suitable for HTMX integration.

    Args:
        request: The workflow request containing pdf_text and query

    Returns:
        HTML response with generated content or error message
    """
    try:
        # Generate a unique thread ID for this request
        thread_id = str(uuid.uuid4())

        result = await run_educational_workflow(
            pdf_text=request.pdf_text,
            user_query=request.query,
            thread_id=thread_id,
        )

        if result["status"] == "success":
            media_html = ""
            if result["media_type"] and result["media_path"]:
                if result["media_type"].startswith("video"):
                    media_html = f"""
                    <video controls autoplay class="generated-media">
                        <source src="{result["media_path"]}" type="{result["media_type"]}">
                        Your browser does not support video playback.
                    </video>
                    """
                else:
                    media_html = f"""
                    <img src="{result["media_path"]}" alt="Generated visualization" class="generated-media">
                    """

            return f"""
            <div class="result success">
                <div class="result-header">
                    <span class="badge curriculum">{result["curriculum"].title()}</span>
                    <span class="badge intention">{result["intention"].title()}</span>
                </div>
                {media_html}
                <details class="code-details">
                    <summary>View Manim Code</summary>
                    <pre><code class="language-python">{result.get("manim_code", "")}</code></pre>
                </details>
            </div>
            """
        else:
            return f"""
            <div class="result error">
                <h4>Generation Failed</h4>
                <p class="error-message">{result.get("error", "Unknown error occurred")}</p>
                <details class="code-details">
                    <summary>View Generated Code (may contain errors)</summary>
                    <pre><code class="language-python">{result.get("manim_code", "No code generated")}</code></pre>
                </details>
            </div>
            """

    except Exception as e:
        return f"""
        <div class="result error">
            <h4>Error</h4>
            <p class="error-message">{str(e)}</p>
        </div>
        """


@router.post("/generate-json", response_model=EducationalWorkflowResponse)
async def generate_content_json(
    request: EducationalWorkflowRequest = Body(...),
) -> EducationalWorkflowResponse:
    """Generate educational content and return JSON response.

    This endpoint is useful for programmatic access or when building
    custom frontends.

    Args:
        request: The workflow request containing pdf_text and query

    Returns:
        JSON response with workflow results

    Raises:
        HTTPException: If an error occurs during processing
    """
    try:
        thread_id = str(uuid.uuid4())

        result = await run_educational_workflow(
            pdf_text=request.pdf_text,
            user_query=request.query,
            thread_id=thread_id,
        )

        return EducationalWorkflowResponse(
            status=result["status"],
            media_path=result.get("media_path"),
            media_type=result.get("media_type"),
            curriculum=result["curriculum"],
            intention=result["intention"],
            error=result.get("error"),
            manim_code=result.get("manim_code"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve", response_class=HTMLResponse)
async def improve_code(
    pdf_text: str = Body(...),
    query: str = Body(...),
    existing_code: str = Body(...),
) -> str:
    """Improve existing Manim code based on user feedback.

    This endpoint is specifically for improving existing code rather than
    generating new content.

    Args:
        pdf_text: Original PDF content for context
        query: User's improvement request
        existing_code: The existing Manim code to improve

    Returns:
        HTML response with improved content
    """
    try:
        thread_id = str(uuid.uuid4())

        result = await run_educational_workflow(
            pdf_text=pdf_text,
            user_query=query,
            thread_id=thread_id,
            existing_code=existing_code,
        )

        if result["status"] == "success":
            media_html = ""
            if result["media_type"] and result["media_path"]:
                if result["media_type"].startswith("video"):
                    media_html = f"""
                    <video controls autoplay class="generated-media">
                        <source src="{result["media_path"]}" type="{result["media_type"]}">
                    </video>
                    """
                else:
                    media_html = f"""
                    <img src="{result["media_path"]}" alt="Improved visualization" class="generated-media">
                    """

            return f"""
            <div class="result success">
                <div class="result-header">
                    <span class="badge">Improved</span>
                </div>
                {media_html}
                <details class="code-details" open>
                    <summary>View Improved Code</summary>
                    <pre><code class="language-python">{result.get("manim_code", "")}</code></pre>
                </details>
            </div>
            """
        else:
            return f"""
            <div class="result error">
                <h4>Improvement Failed</h4>
                <p class="error-message">{result.get("error", "Unknown error")}</p>
            </div>
            """

    except Exception as e:
        return f"""
        <div class="result error">
            <h4>Error</h4>
            <p class="error-message">{str(e)}</p>
        </div>
        """
