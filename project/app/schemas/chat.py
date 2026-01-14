"""Pydantic schemas for chat API requests and responses."""

from typing import Optional, List
from pydantic import BaseModel, Field, constr


# Request Schemas

class ChatMessageRequest(BaseModel):
    """Request to send a message in a chat."""
    message: str = Field(..., min_length=1, max_length=5000, description="Message text")
    chat_id: str = Field(..., description="Chat ID to send message to")
    file_id: Optional[str] = Field(None, description="Optional file ID for PDF context")


class NewChatRequest(BaseModel):
    """Request to create a new chat."""
    title: Optional[str] = Field(None, max_length=200, description="Optional chat title")


# Response Schemas

class ChatResponse(BaseModel):
    """Response after creating a chat or sending a message."""
    chat_id: str = Field(..., description="Chat ID")
    message_id: Optional[str] = Field(None, description="Message ID (if message was sent)")
    status: str = Field(..., description="Status: processing | completed | failed")


class ChatMetadata(BaseModel):
    """Chat metadata for sidebar display."""
    chat_id: str
    title: str
    created_at: str
    session_id: str


class Message(BaseModel):
    """Individual chat message."""
    role: constr(pattern="^(user|assistant)$") = Field(..., description="Message role")
    content: str = Field(..., description="Message text content")
    media_url: Optional[str] = Field(None, description="URL to image/video")
    media_type: Optional[str] = Field(None, description="Media MIME type")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class ChatMessagesResponse(BaseModel):
    """Response containing chat messages."""
    chat_id: str
    messages: List[Message]


class AgentMultiMediaResponse(BaseModel):
    """
    Response from agent with text and optional media.

    Used when agent generates images/videos in addition to text.
    """
    text: str = Field(..., description="Text response from agent")
    media_url: Optional[str] = Field(None, description="URL to generated image/video")
    media_type: Optional[str] = Field(
        None,
        description="Media MIME type",
        pattern="^(image/(png|jpeg|jpg|gif|webp)|video/mp4)$"
    )


class FileUploadResponse(BaseModel):
    """Response after PDF upload."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    extracted_text_preview: str = Field(..., description="Preview of extracted text (first 500 chars)")
    text_length: int = Field(..., description="Total length of extracted text")
    status: str = Field(..., description="Status: success | error")
    error: Optional[str] = Field(None, description="Error message if status is error")


class ChatStatusResponse(BaseModel):
    """Response for checking async chat status."""
    status: str = Field(..., description="Status: processing | completed | failed")
    result: Optional[AgentMultiMediaResponse] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class ChatListResponse(BaseModel):
    """Response containing user's chat list."""
    session_id: str
    chats: List[ChatMetadata]


# Validation Schemas

class SessionInfo(BaseModel):
    """Session information."""
    session_id: str = Field(..., description="User session ID")
    chat_count: int = Field(..., description="Number of chats in session")
    session_exists: bool = Field(..., description="Whether session has data")
