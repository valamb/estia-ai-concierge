from fastapi import APIRouter
from app.api.routes import health, chat, info, voice, image

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(info.router)
api_router.include_router(chat.router, prefix="/api/v1")
api_router.include_router(voice.router, prefix="/api/v1")
api_router.include_router(image.router, prefix="/api/v1")

__all__ = ["api_router"]
