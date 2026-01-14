from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from typing import Optional

from project.app.services import chat_service

router = APIRouter(tags=["Frontend"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main chat interface - redirects to chat page."""
    templates = request.app.state.templates
    session_id = get_or_create_session_id(request)

    response = templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "chat_id": None,
            "chat_title": None,
            "file_id": None
        }
    )
    # Set session cookie if not exists
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id, max_age=86400)
    return response


@router.get("/components/agent-status", response_class=HTMLResponse)
async def agent_status(request: Request):
    """HTMX partial: Agent status component (auto-refreshing)"""
    templates = request.app.state.templates
    # In a real app, fetch status from database or cache
    status = {"agents_active": 3, "tasks_completed": 42, "tasks_pending": 5}
    return templates.TemplateResponse(
        "components/agent_status.html", {"request": request, "status": status}
    )


# Chat Routes

def get_or_create_session_id(request: Request) -> str:
    """Get or create session ID from cookies."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = chat_service.generate_session_id()
    return session_id


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, file_id: Optional[str] = None):
    """Main chat page - initial state with PDF upload."""
    templates = request.app.state.templates
    session_id = get_or_create_session_id(request)

    response = templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "chat_id": None,
            "chat_title": None,
            "file_id": file_id
        }
    )
    # Set session cookie if not exists
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id, max_age=86400)
    return response


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def chat_detail_page(
    request: Request,
    chat_id: str,
    file_id: Optional[str] = None
):
    """Chat page with specific chat loaded."""
    templates = request.app.state.templates
    session_id = get_or_create_session_id(request)

    # Get chat metadata
    chat_metadata = chat_service.get_chat_metadata(chat_id)
    if not chat_metadata:
        # Chat not found, redirect to main page
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "session_id": session_id,
                "chat_id": None,
                "error": "Chat not found"
            }
        )

    response = templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "chat_id": chat_id,
            "chat_title": chat_metadata.get("title", "Chat"),
            "file_id": file_id
        }
    )
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id, max_age=86400)
    return response


@router.get("/components/chat-sidebar", response_class=HTMLResponse)
async def chat_sidebar_component(request: Request, session_id: str):
    """HTMX partial: Chat sidebar with history."""
    templates = request.app.state.templates

    # Get user's chats
    chats = chat_service.get_user_chats(session_id)
    current_chat_id = request.query_params.get("current_chat_id")

    return templates.TemplateResponse(
        "components/chat_sidebar.html",
        {
            "request": request,
            "chats": chats,
            "current_chat_id": current_chat_id
        }
    )


@router.get("/components/chat-messages/{chat_id}", response_class=HTMLResponse)
async def chat_messages_component(request: Request, chat_id: str):
    """HTMX partial: Chat messages for a specific chat."""
    templates = request.app.state.templates

    # Get messages
    messages = chat_service.get_chat_messages(chat_id)

    return templates.TemplateResponse(
        "components/chat_messages.html",
        {
            "request": request,
            "messages": messages,
            "chat_id": chat_id
        }
    )


@router.get("/components/chat-input", response_class=HTMLResponse)
async def chat_input_component(
    request: Request,
    chat_id: str,
    file_id: Optional[str] = None
):
    """HTMX partial: Chat input form."""
    templates = request.app.state.templates

    return templates.TemplateResponse(
        "components/chat_input.html",
        {
            "request": request,
            "chat_id": chat_id,
            "file_id": file_id
        }
    )


@router.get("/components/chat-carousel", response_class=HTMLResponse)
async def chat_carousel_component(request: Request):
    """HTMX partial: Image carousel with examples."""
    templates = request.app.state.templates

    return templates.TemplateResponse(
        "components/image_carousel.html",
        {"request": request}
    )


@router.get("/components/chat-content/{chat_id}", response_class=HTMLResponse)
async def chat_content_component(
    request: Request,
    chat_id: str,
    file_id: Optional[str] = None
):
    """HTMX partial: Chat content (header + messages + input) for swapping."""
    templates = request.app.state.templates

    # Get chat metadata
    chat_metadata = chat_service.get_chat_metadata(chat_id)
    if not chat_metadata:
        return "<div class='error'>Chat not found</div>"

    return templates.TemplateResponse(
        "components/chat_content.html",
        {
            "request": request,
            "chat_id": chat_id,
            "chat_title": chat_metadata.get("title", "Chat"),
            "file_id": file_id
        }
    )


@router.get("/components/initial-view", response_class=HTMLResponse)
async def initial_view_component(request: Request):
    """HTMX partial: Initial view with PDF upload for new chat."""
    templates = request.app.state.templates

    return templates.TemplateResponse(
        "components/initial_view.html",
        {"request": request}
    )
