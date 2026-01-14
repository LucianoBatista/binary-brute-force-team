from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Frontend"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page with HTMX"""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Binary Brute Force Team - Agent Dashboard"}
    )


@router.get("/components/agent-status", response_class=HTMLResponse)
async def agent_status(request: Request):
    """HTMX partial: Agent status component (auto-refreshing)"""
    templates = request.app.state.templates
    # In a real app, fetch status from database or cache
    status = {
        "agents_active": 3,
        "tasks_completed": 42,
        "tasks_pending": 5
    }
    return templates.TemplateResponse(
        "components/agent_status.html",
        {"request": request, "status": status}
    )
