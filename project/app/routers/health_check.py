from fastapi import status
from project.app.routers import health_check_router


@health_check_router.get("", status_code=status.HTTP_200_OK)
def health_check():
    return {"Status": "ok"}