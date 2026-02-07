from app.routers.auth import router as auth_router
from app.routers.quiz import router as quiz_router
from app.routers.attempt import router as attempt_router
from app.routers.user import router as user_router
from app.routers.chat import router as chat_router

__all__ = [
    "auth_router",
    "quiz_router",
    "attempt_router",
    "user_router",
    "chat_router",
]
