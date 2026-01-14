"""Chat API router for handling chat sessions, messages, and PDF uploads."""

from typing import Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from project.app.agents.educational_workflow import run_educational_workflow
from project.app.agents.simple_agent import run_simple_agent
from project.app.schemas.chat import (
    ChatListResponse,
    ChatMetadata,
    ChatResponse,
    NewChatRequest,
)
from project.app.services import chat_service, pdf_service

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
async def create_new_chat(request: Request, body: NewChatRequest = Body(...)):
    """
    Create a new chat session.

    Creates a new chat and adds it to the user's session chat list.

    Returns:
        ChatResponse: Contains new chat_id
    """
    try:
        session_id = get_session_id(request)
        chat_id = chat_service.create_chat(session_id, title=body.title)

        return ChatResponse(chat_id=chat_id, status="completed")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create new chat: {str(e)}"
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
            session_id=session_id, chats=[ChatMetadata(**chat) for chat in chats]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat list: {str(e)}"
        )


@router.post("/upload-pdf", response_class=HTMLResponse)
async def upload_pdf_file(request: Request, file: UploadFile = File(...)):
    """
    Upload PDF, extract text via OCR, run workflow, and create chat.

    Workflow:
    1. Process PDF (validate + OCR)
    2. Store PDF data in Redis
    3. Run educational workflow to generate media
    4. Create chat with detected concept as title
    5. Store context for re-interactions
    6. Add assistant message with media
    7. Redirect to chat view

    Returns:
        HTMLResponse: JavaScript redirect to chat page
    """
    try:
        # Step 1: Process PDF (validate + OCR)
        file_id, extracted_text, file_path, error = await pdf_service.process_pdf(file)

        if error:
            return f"""
            <div class="result error">
                <p><strong>Erro no upload:</strong> {error}</p>
            </div>
            """

        # Step 2: Store PDF data in Redis
        chat_service.store_file_data(
            file_id=file_id,
            file_path=file_path,
            extracted_text=extracted_text,
            original_filename=file.filename or "unknown.pdf",
        )

        # Step 3: Run educational workflow (auto-generate)
        result = await run_educational_workflow(pdf_text=extracted_text)

        # Step 4: Create chat with detected concept as title
        session_id = get_session_id(request)
        detected_concepts = result.get("detected_concepts", [])
        chat_title = (
            detected_concepts[0] if detected_concepts else file.filename or "documento"
        )
        chat_id = chat_service.create_chat(session_id, title=chat_title)

        # Step 5: Store context for re-interactions
        chat_service.store_chat_context(
            chat_id=chat_id,
            file_id=file_id,
            manim_code=result.get("manim_code", ""),
            pdf_text=extracted_text,
        )

        # Step 6: Add assistant message with media
        media_path = result.get("media_path", "")
        media_type = result.get("media_type", "")
        status = result.get("status", "failed")

        if status == "success":
            chat_service.add_message(
                chat_id=chat_id,
                role="assistant",
                content="Visualização gerada com sucesso!",
                media_url=media_path,
                media_type=media_type,
            )
        else:
            error_msg = result.get("error", "Erro na geração da visualização")
            chat_service.add_message(
                chat_id=chat_id, role="assistant", content=f"Erro: {error_msg}"
            )

        # Step 7: Redirect to chat view
        return f"""
        <script>
            window.location.href = '/chat/{chat_id}';
        </script>
        """

    except Exception as e:
        return f"""
        <div class="result error">
            <p><strong>Erro:</strong> {str(e)}</p>
        </div>
        """


@router.post("/message", response_class=HTMLResponse)
async def send_message(
    message: str = Form(...),
    chat_id: str = Form(...),
    file_id: Optional[str] = Form(None),
):
    """
    Send a message in a chat and get agent response.

    Uses educational_workflow for PDF-based chats (re-interactions).
    Uses simple_agent for regular chats.

    Returns:
        HTMLResponse: Message bubble HTML for HTMX swap
    """
    try:
        # Add user message
        user_message = chat_service.add_message(
            chat_id=chat_id, role="user", content=message
        )

        # Get chat context (PDF text + existing Manim code)
        context = chat_service.get_chat_context(chat_id)

        if context and context.get("pdf_text"):
            # PDF-based chat: use educational workflow for re-interaction
            result = await run_educational_workflow(
                pdf_text=context.get("pdf_text", ""),
                user_query=message,
                existing_code=context.get("manim_code"),  # Enables improvement mode
            )

            status = result.get("status", "failed")

            if status == "success":
                response_text = "Visualização atualizada!"
                media_url = result.get("media_path")
                media_type = result.get("media_type")

                # Update stored Manim code for next iteration
                if result.get("manim_code"):
                    chat_service.update_chat_context(
                        chat_id=chat_id, manim_code=result.get("manim_code")
                    )
            else:
                response_text = f"Erro: {result.get('error', 'Erro na geração')}"
                media_url = None
                media_type = None
        else:
            # Regular chat: use simple agent
            agent_result = await run_simple_agent(message)

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
            media_type=media_type,
        )

        # Build HTML response
        html_parts = [
            '<div class="message-group">',
            '<div class="message user-message">',
            f'  <div class="message-content">{message}</div>',
            f'  <div class="message-timestamp">{user_message["timestamp"]}</div>',
            "</div>",
            '<div class="message assistant-message">',
            f'  <div class="message-content">{response_text}</div>',
        ]

        # Add media if present
        if media_url and media_type:
            if media_type.startswith("video/"):
                html_parts.append(
                    f'  <div class="message-media">'
                    f'    <video src="{media_url}" controls autoplay class="generated-video"></video>'
                    f"  </div>"
                )
            elif media_type.startswith("image/"):
                html_parts.append(
                    f'  <div class="message-media">'
                    f'    <img src="{media_url}" alt="Generated" class="generated-image">'
                    f"  </div>"
                )

        html_parts.extend(
            [
                f'  <div class="message-timestamp">{agent_message["timestamp"]}</div>',
                "</div>",
                "</div>",
            ]
        )

        return "".join(html_parts)

    except Exception as e:
        error_html = f"""
        <div class="message-group error">
            <div class="message assistant-message error-message">
                <div class="message-content">
                    <strong>Erro:</strong> {str(e)}
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
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")
