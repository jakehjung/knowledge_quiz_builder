from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    auth_router,
    quiz_router,
    attempt_router,
    user_router,
    chat_router,
)

settings = get_settings()

app = FastAPI(
    title="AI-Powered Knowledge Quiz Builder",
    description="API for creating and taking AI-generated quizzes",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(quiz_router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(attempt_router, prefix="/api/attempts", tags=["Quiz Attempts"])
app.include_router(user_router, prefix="/api/users", tags=["Users"])
app.include_router(chat_router, prefix="/api/chat", tags=["AI Chat"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
