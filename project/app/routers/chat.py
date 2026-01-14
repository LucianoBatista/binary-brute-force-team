"""Chat API router for handling chat sessions, messages, and PDF uploads."""

from fastapi import APIRouter, Body, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from typing import Optional

from project.app.schemas.chat import (
    NewChatRequest,
    ChatResponse,
    ChatMessageRequest,
    FileUploadResponse,
    ChatStatusResponse,
    ChatListResponse,
    AgentMultiMediaResponse,
    ChatMetadata,
)
from project.app.services import chat_service, pdf_service
from project.app.agents.simple_agent import run_simple_agent

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def get_session_id(request: Request) -> str:
    """
    Get or create session ID from cookies.

    Args:
        request: FastAPI request object

    Returns:
        str: Session ID
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        # Generate new session ID if not exists
        session_id = chat_service.generate_session_id()
    return session_id


@router.post("/new", response_model=ChatResponse)
async def create_new_chat(
    request: Request,
    body: NewChatRequest = Body(...)
):
    """
    Create a new chat session.

    Creates a new chat and adds it to the user's session chat list.

    Returns:
        ChatResponse: Contains new chat_id
    """
    try:
        session_id = get_session_id(request)
        chat_id = chat_service.create_chat(session_id, title=body.title)

        return ChatResponse(
            chat_id=chat_id,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create new chat: {str(e)}"
        )


@router.get("/list", response_model=ChatListResponse)
async def get_chat_list(request: Request):
    """
    Get all chats for the current session.

    Returns:
        ChatListResponse: List of chat metadata
    """
    try:
        session_id = get_session_id(request)
        chats = chat_service.get_user_chats(session_id)

        return ChatListResponse(
            session_id=session_id,
            chats=[ChatMetadata(**chat) for chat in chats]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat list: {str(e)}"
        )


@router.post("/upload-pdf", response_model=FileUploadResponse)
async def upload_pdf_file(file: UploadFile = File(...)):
    """
    Upload PDF file and extract text using Mistral OCR.

    Workflow:
    1. Validate file (type, size)
    2. Save to temporary storage
    3. Extract text using Mistral OCR
    4. Store file data in Redis
    5. Return file_id for use in messages

    Returns:
        FileUploadResponse: Contains file_id and extracted text preview
    """
    try:
        # Process PDF
        file_id, extracted_text, file_path, error = await pdf_service.process_pdf(file)

        if error:
            return FileUploadResponse(
                file_id="",
                filename=file.filename or "unknown",
                extracted_text_preview="",
                text_length=0,
                status="error",
                error=error
            )

        # Store file data in Redis
        chat_service.store_file_data(
            file_id=file_id,
            file_path=file_path,
            extracted_text=extracted_text,
            original_filename=file.filename or "unknown.pdf"
        )

        # Create preview (first 500 characters)
        preview = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename or "unknown.pdf",
            extracted_text_preview=preview,
            text_length=len(extracted_text),
            status="success",
            error=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.post("/message", response_class=HTMLResponse)
async def send_message(
    message: str = Form(...),
    chat_id: str = Form(...),
    file_id: Optional[str] = Form(None)
):
    """
    Send a message in a chat and get agent response.

    Workflow:
    1. Add user message to chat
    2. Retrieve PDF text if file_id provided
    3. Send to multi-agent system
    4. Add agent response to chat
    5. Return HTML for HTMX display

    Returns:
        HTMLResponse: Message bubble HTML for HTMX swap
    """
    try:
        # Add user message
        user_message = chat_service.add_message(
            chat_id=chat_id,
            role="user",
            content=message
        )

        # Retrieve PDF text if file_id provided
        query = message
        if file_id:
            file_data = chat_service.get_file_data(file_id)
            if file_data:
                pdf_text = file_data.get("extracted_text", "")
                # Combine PDF text with user message
                query = f"Context from PDF:\n{pdf_text}\n\nUser question: {message}"

        # Call agent
        agent_result = await run_simple_agent(query)

        # Parse agent result (could be string or dict with media)
        if isinstance(agent_result, dict):
            response_text = agent_result.get("text", str(agent_result))
            media_url = agent_result.get("media_url")
            media_type = agent_result.get("media_type")
        else:
            response_text = str(agent_result)
            media_url = None
            media_type = None

        # Add agent response to chat
        agent_message = chat_service.add_message(
            chat_id=chat_id,
            role="assistant",
            content=response_text,
            media_url=media_url,
            media_type=media_type
        )

        # Build HTML response
        html_parts = [
            '<div class="message-group">',
            # User message
            f'<div class="message user-message">',
            f'  <div class="message-content">{message}</div>',
            f'  <div class="message-timestamp">{user_message["timestamp"]}</div>',
            f'</div>',
            # Agent message
            f'<div class="message assistant-message">',
            f'  <div class="message-content">{response_text}</div>',
        ]

        # Add media if present
        if media_url and media_type:
            if media_type.startswith("image/"):
                html_parts.append(
                    f'  <div class="message-media">'
                    f'    <img src="{media_url}" alt="Generated image" class="generated-image">'
                    f'  </div>'
                )
            elif media_type.startswith("video/"):
                html_parts.append(
                    f'  <div class="message-media">'
                    f'    <video src="{media_url}" controls class="generated-video"></video>'
                    f'  </div>'
                )

        html_parts.extend([
            f'  <div class="message-timestamp">{agent_message["timestamp"]}</div>',
            f'</div>',
            '</div>'
        ])

        return "".join(html_parts)

    except Exception as e:
        # Return error HTML
        error_html = f"""
        <div class="message-group error">
            <div class="message assistant-message error-message">
                <div class="message-content">
                    <strong>Error:</strong> {str(e)}
                </div>
            </div>
        </div>
        """
        return error_html


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    """
    Delete a chat and all its messages.

    Args:
        chat_id: Chat ID to delete

    Returns:
        dict: Success message
    """
    try:
        success = chat_service.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"status": "success", "message": "Chat deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat: {str(e)}"
        )
