"""Quiz routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_instructor
from app.schemas.quiz import (
    QuizCreate,
    QuizListResponse,
    QuizResponse,
    QuizResponseForStudent,
    QuizUpdate,
    SortOrder,
)
from app.schemas.user import UserResponse
from app.services.analytics_service import AnalyticsService
from app.services.quiz_service import QuizService

router = APIRouter()


@router.get("", response_model=QuizListResponse)
async def list_quizzes(
    search: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    sort: SortOrder = Query(SortOrder.NEWEST),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await QuizService(db).list_quizzes(
        search=search, tags=tags, sort=sort, page=page, page_size=page_size
    )


@router.get("/my", response_model=QuizListResponse)
async def get_my_quizzes(
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    return await QuizService(db).get_instructor_quizzes(current_user.id)


@router.get("/my/stats")
async def get_instructor_stats(
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService(db).get_instructor_dashboard_stats(current_user.id)


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quiz = await QuizService(db).get_quiz_by_id(quiz_id)

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )

    # Instructor sees full details, others see student view (no answers)
    if quiz.instructor_id == current_user.id:
        return QuizResponse.from_orm_with_tags(quiz)
    return QuizResponseForStudent.from_orm_with_tags(quiz)


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    quiz = await QuizService(db).create_quiz(quiz_data, current_user.id)
    return QuizResponse.from_orm_with_tags(quiz)


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: UUID,
    update_data: QuizUpdate,
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    quiz = await QuizService(db).update_quiz(quiz_id, update_data, current_user.id)

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or you don't have permission to edit it",
        )

    return QuizResponse.from_orm_with_tags(quiz)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    success = await QuizService(db).delete_quiz(quiz_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or you don't have permission to delete it",
        )


@router.get("/{quiz_id}/analytics")
async def get_quiz_analytics(
    quiz_id: UUID,
    current_user: UserResponse = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
):
    quiz = await QuizService(db).get_quiz_by_id(quiz_id)

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )

    if quiz.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view analytics for this quiz",
        )

    return await AnalyticsService(db).get_quiz_analytics(quiz_id)
