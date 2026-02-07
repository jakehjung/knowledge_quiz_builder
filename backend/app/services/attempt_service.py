from uuid import UUID
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptStatus
from app.schemas.attempt import (
    AttemptResultResponse,
    QuestionResultResponse,
    AttemptSummary,
    UserAttemptsResponse,
    AttemptAnswerSave,
)


class AttemptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_attempt(self, quiz_id: UUID, user_id: UUID) -> QuizAttempt:
        # Check if there's an in-progress attempt to resume
        # Use scalars().first() to handle case where multiple in-progress attempts exist
        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.status == AttemptStatus.IN_PROGRESS,
                )
            )
            .order_by(QuizAttempt.started_at.desc())
        )
        existing_attempt = result.scalars().first()

        if existing_attempt:
            return existing_attempt

        # Get quiz questions
        quiz_result = await self.db.execute(
            select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
        )
        quiz = quiz_result.scalar_one_or_none()

        if not quiz:
            raise ValueError("Quiz not found")

        # Create new attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            status=AttemptStatus.IN_PROGRESS,
        )
        self.db.add(attempt)
        await self.db.flush()

        # Create empty answer slots for each question
        for question in quiz.questions:
            answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_answer=None,
                is_correct=None,
            )
            self.db.add(answer)

        await self.db.commit()
        await self.db.refresh(attempt)

        # Reload with relationships
        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == attempt.id)
        )
        return result.scalar_one()

    async def save_progress(
        self, attempt_id: UUID, user_id: UUID, answers: List[AttemptAnswerSave]
    ) -> Optional[QuizAttempt]:
        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(
                and_(
                    QuizAttempt.id == attempt_id,
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.status == AttemptStatus.IN_PROGRESS,
                )
            )
        )
        attempt = result.scalar_one_or_none()

        if not attempt:
            return None

        # Update answers
        answer_map = {str(a.question_id): a for a in attempt.answers}
        for ans_data in answers:
            if str(ans_data.question_id) in answer_map:
                answer_map[
                    str(ans_data.question_id)
                ].selected_answer = ans_data.selected_answer

        await self.db.commit()

        # Reload the attempt with its answers to get fresh data
        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == attempt_id)
        )
        return result.scalar_one()

    async def submit_attempt(
        self, attempt_id: UUID, user_id: UUID, answers: List[AttemptAnswerSave]
    ) -> Optional[AttemptResultResponse]:
        result = await self.db.execute(
            select(QuizAttempt)
            .options(
                selectinload(QuizAttempt.answers),
                selectinload(QuizAttempt.quiz).selectinload(Quiz.questions),
            )
            .where(
                and_(
                    QuizAttempt.id == attempt_id,
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.status == AttemptStatus.IN_PROGRESS,
                )
            )
        )
        attempt = result.scalar_one_or_none()

        if not attempt:
            return None

        # Build question map for correct answers
        question_map = {str(q.id): q for q in attempt.quiz.questions}
        answer_map = {str(a.question_id): a for a in attempt.answers}

        # Update answers with final selections and correctness
        score = 0
        for ans_data in answers:
            if str(ans_data.question_id) in answer_map:
                answer = answer_map[str(ans_data.question_id)]
                answer.selected_answer = ans_data.selected_answer

                question = question_map.get(str(ans_data.question_id))
                if question and ans_data.selected_answer:
                    is_correct = ans_data.selected_answer == question.correct_answer
                    answer.is_correct = is_correct
                    if is_correct:
                        score += 1
                else:
                    answer.is_correct = False

        # Update attempt status
        attempt.status = AttemptStatus.COMPLETED
        attempt.score = score
        attempt.completed_at = datetime.utcnow()

        await self.db.commit()

        # Build result response
        question_results = []
        for question in sorted(attempt.quiz.questions, key=lambda q: q.order_index):
            answer = answer_map.get(str(question.id))
            question_results.append(
                QuestionResultResponse(
                    id=question.id,
                    question_text=question.question_text,
                    option_a=question.option_a,
                    option_b=question.option_b,
                    option_c=question.option_c,
                    option_d=question.option_d,
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                    selected_answer=answer.selected_answer if answer else None,
                    is_correct=answer.is_correct if answer else False,
                )
            )

        return AttemptResultResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            quiz_title=attempt.quiz.title,
            status=attempt.status,
            score=attempt.score,
            total_questions=len(attempt.quiz.questions),
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            questions=question_results,
        )

    async def get_attempt(
        self, attempt_id: UUID, user_id: UUID
    ) -> Optional[AttemptResultResponse]:
        result = await self.db.execute(
            select(QuizAttempt)
            .options(
                selectinload(QuizAttempt.answers),
                selectinload(QuizAttempt.quiz).selectinload(Quiz.questions),
            )
            .where(
                and_(
                    QuizAttempt.id == attempt_id,
                    QuizAttempt.user_id == user_id,
                )
            )
        )
        attempt = result.scalar_one_or_none()

        if not attempt:
            return None

        answer_map = {str(a.question_id): a for a in attempt.answers}

        question_results = []
        for question in sorted(attempt.quiz.questions, key=lambda q: q.order_index):
            answer = answer_map.get(str(question.id))
            question_results.append(
                QuestionResultResponse(
                    id=question.id,
                    question_text=question.question_text,
                    option_a=question.option_a,
                    option_b=question.option_b,
                    option_c=question.option_c,
                    option_d=question.option_d,
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                    selected_answer=answer.selected_answer if answer else None,
                    is_correct=answer.is_correct if answer else None,
                )
            )

        return AttemptResultResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            quiz_title=attempt.quiz.title,
            status=attempt.status,
            score=attempt.score,
            total_questions=len(attempt.quiz.questions),
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            questions=question_results,
        )

    async def get_user_attempts(self, user_id: UUID) -> UserAttemptsResponse:
        from app.models.quiz import Quiz

        result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.quiz).selectinload(Quiz.questions))
            .where(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.started_at.desc())
        )
        attempts = result.scalars().all()

        attempt_summaries = [
            AttemptSummary(
                id=a.id,
                quiz_id=a.quiz_id,
                quiz_title=a.quiz.title,
                status=a.status,
                score=a.score,
                total_questions=len(a.quiz.questions),
                started_at=a.started_at,
                completed_at=a.completed_at,
            )
            for a in attempts
        ]

        return UserAttemptsResponse(
            attempts=attempt_summaries, total=len(attempt_summaries)
        )
