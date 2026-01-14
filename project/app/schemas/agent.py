from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Request model for agent execution"""
    query: str = Field(..., min_length=1, description="The query to process")


class AgentResponse(BaseModel):
    """Response model for agent execution"""
    status: str = Field(..., description="Execution status (success/error)")
    result: str = Field(..., description="Agent execution result")
    html: str | None = Field(None, description="Optional HTML fragment for HTMX")


class AgentTaskResponse(BaseModel):
    """Response model for async agent tasks"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")


class AgentTaskStatusResponse(BaseModel):
    """Response model for async task status checks"""
    status: str = Field(..., description="Current task status (processing/completed/failed)")
    result: str | None = Field(None, description="Result if task is completed")
    error: str | None = Field(None, description="Error message if task failed")
