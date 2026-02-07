"""Quiz attempt routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.attempt import (
    AttemptAnswerSave,
    AttemptResponse,
    AttemptResultResponse,
    UserAttemptsResponse,
)
from app.schemas.user import UserResponse
from app.services.attempt_service import AttemptService

router = APIRouter()


@router.post("/{quiz_id}/start", response_model=AttemptResponse)
async def start_attempt(
    quiz_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        attempt = await AttemptService(db).start_attempt(quiz_id, current_user.id)
        return AttemptResponse.model_validate(attempt)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{attempt_id}", response_model=AttemptResponse)
async def save_progress(
    attempt_id: UUID,
    request: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    answers = [AttemptAnswerSave(**a) for a in request.get("answers", [])]
    attempt = await AttemptService(db).save_progress(
        attempt_id, current_user.id, answers
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found or already completed",
        )

    return AttemptResponse.model_validate(attempt)


@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
async def submit_attempt(
    attempt_id: UUID,
    request: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    answers = [AttemptAnswerSave(**a) for a in request.get("answers", [])]
    result = await AttemptService(db).submit_attempt(
        attempt_id, current_user.id, answers
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found or already completed",
        )

    return result


@router.get("/my", response_model=UserAttemptsResponse)
async def get_my_attempts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AttemptService(db).get_user_attempts(current_user.id)


@router.get("/{attempt_id}", response_model=AttemptResultResponse)
async def get_attempt(
    attempt_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await AttemptService(db).get_attempt(attempt_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found"
        )

    return result
