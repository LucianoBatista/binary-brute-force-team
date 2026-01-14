from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import HTMLResponse
from project.app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentTaskResponse,
    AgentTaskStatusResponse
)
from project.app.agents.simple_agent import run_simple_agent

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.post("/execute", response_class=HTMLResponse)
async def execute_agent(request: AgentRequest = Body(...)):
    """
    Execute LangGraph agent synchronously.
    Returns HTML fragment for HTMX compatibility.

    This endpoint runs the agent workflow and returns results immediately.
    For long-running tasks, use the /execute-async endpoint instead.
    """
    try:
        # Run the agent
        result = await run_simple_agent(request.query)

        # Return HTML fragment for HTMX
        html = f"""
        <div class="result success">
            <h4>Agent Response:</h4>
            <p>{result}</p>
        </div>
        """
        return html

    except Exception as e:
        # Return error HTML fragment
        error_html = f"""
        <div class="result error">
            <h4>Error:</h4>
            <p>{str(e)}</p>
        </div>
        """
        return error_html


@router.post("/execute-async", response_model=AgentTaskResponse)
async def execute_agent_async(request: AgentRequest):
    """
    Execute LangGraph agent asynchronously via Celery.
    Returns task ID for status polling.

    Use this endpoint for long-running agent workflows.
    Poll /task/{task_id} to check status and retrieve results.
    """
    try:
        from project.app.celery.tasks import run_agent_async
        task = run_agent_async.delay(request.query)
        return AgentTaskResponse(
            task_id=task.id,
            status="processing"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start async task: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=AgentTaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Check the status of an async agent task.

    Returns:
        - status="processing" if task is still running
        - status="completed" with result if task finished successfully
        - status="failed" with error if task failed
    """
    try:
        from project.app.celery.tasks import run_agent_async
        from celery.result import AsyncResult

        task = AsyncResult(task_id)

        if task.ready():
            if task.successful():
                return AgentTaskStatusResponse(
                    status="completed",
                    result=task.result
                )
            else:
                return AgentTaskStatusResponse(
                    status="failed",
                    error=str(task.info)
                )
        else:
            return AgentTaskStatusResponse(
                status="processing"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check task status: {str(e)}"
        )
