"""AI chat routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_instructor
from app.schemas.chat import ChatMessage, ChatResponse
from app.schemas.user import UserResponse
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await AIService(
            db, current_user.id, current_user.theme_preference
        ).chat(message.message, message.conversation_history)

        return ChatResponse(
            response=result["response"],
            action_taken=result.get("action_taken"),
            data=result.get("data"),
        )
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}",
        )
