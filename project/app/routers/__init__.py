from fastapi import APIRouter

health_check_router = APIRouter(prefix="/health", tags=["Health"])
# add other router here

# import others routers here
from . import health_check  # noqa: E402 F401
