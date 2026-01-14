"""Schemas for the educational content generation workflow."""

from typing import Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Type aliases for routing
CurriculumComponent = Literal["math", "chemistry", "physics", "unknown"]
IntentionType = Literal["static", "dynamic", "improvement"]
ExecutionStatus = Literal["pending", "success", "failed"]


class EducationalState(TypedDict):
    """State schema for the LangGraph educational workflow.

    This TypedDict defines all the state that flows through the multi-agent
    workflow, from intention detection through media generation.
    """

    # Input fields
    pdf_text: str
    user_query: str

    # Intention Detection Results
    curriculum_component: CurriculumComponent
    intention_type: IntentionType
    detected_concepts: list[str]
    analysis_summary: str

    # Content Generation
    manim_code: str
    code_explanation: str

    # Media Generation
    media_path: Optional[str]
    media_type: Optional[str]
    execution_status: ExecutionStatus
    error_message: Optional[str]


class EducationalWorkflowRequest(BaseModel):
    """Request schema for the educational workflow API endpoint."""

    pdf_text: str = Field(
        ...,
        min_length=1,
        description="The extracted text from the PDF document",
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's query or request for content generation",
    )


class EducationalWorkflowResponse(BaseModel):
    """Response schema for the educational workflow API endpoint."""

    status: ExecutionStatus = Field(
        ...,
        description="The execution status of the workflow",
    )
    media_path: Optional[str] = Field(
        None,
        description="Path to the generated media file",
    )
    media_type: Optional[str] = Field(
        None,
        description="MIME type of the generated media (e.g., video/mp4)",
    )
    curriculum: CurriculumComponent = Field(
        ...,
        description="Detected curriculum component",
    )
    intention: IntentionType = Field(
        ...,
        description="Detected user intention type",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if execution failed",
    )
    manim_code: Optional[str] = Field(
        None,
        description="The generated Manim code",
    )


class IntentionDetectionResult(BaseModel):
    """Schema for parsing the intention detector LLM response."""

    curriculum: CurriculumComponent = Field(
        default="unknown",
        description="Detected curriculum component",
    )
    intention: IntentionType = Field(
        default="static",
        description="Detected user intention",
    )
    concepts: list[str] = Field(
        default_factory=list,
        description="List of detected educational concepts",
    )
    summary: str = Field(
        default="",
        description="Brief analysis summary",
    )
