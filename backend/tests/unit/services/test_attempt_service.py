"""Unit tests for AttemptService."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.attempt_service import AttemptService
from app.schemas.attempt import AttemptAnswerSave
from app.models.user import User
from app.models.quiz import Quiz, AnswerOption
from app.models.attempt import QuizAttempt, AttemptStatus

pytestmark = pytest.mark.unit


class TestAttemptServiceStart:
    """Tests for AttemptService.start_attempt method."""

    async def test_start_new_attempt(
        self, db_session: AsyncSession, sample_quiz: Quiz, test_student: User
    ):
        """Test starting a new quiz attempt."""
        service = AttemptService(db_session)

        result = await service.start_attempt(sample_quiz.id, test_student.id)

        assert result is not None
        assert result.quiz_id == sample_quiz.id
        assert result.user_id == test_student.id
        assert result.status == AttemptStatus.IN_PROGRESS
        assert result.score is None
        assert len(result.answers) == 5  # 5 question slots created

    async def test_start_attempt_resumes_existing(
        self, db_session: AsyncSession, sample_attempt: QuizAttempt, test_student: User
    ):
        """Test that starting an attempt resumes existing in-progress attempt."""
        service = AttemptService(db_session)

        result = await service.start_attempt(sample_attempt.quiz_id, test_student.id)

        assert result is not None
        assert result.id == sample_attempt.id
        assert result.status == AttemptStatus.IN_PROGRESS

    async def test_start_attempt_quiz_not_found(
        self, db_session: AsyncSession, test_student: User
    ):
        """Test starting attempt for non-existent quiz raises error."""
        service = AttemptService(db_session)

        with pytest.raises(ValueError, match="Quiz not found"):
            await service.start_attempt(uuid4(), test_student.id)


class TestAttemptServiceSaveProgress:
    """Tests for AttemptService.save_progress method."""

    async def test_save_progress_single_answer(
        self, db_session: AsyncSession, sample_attempt: QuizAttempt, test_student: User
    ):
        """Test saving a single answer."""
        service = AttemptService(db_session)

        # Get first question ID
        result = await db_session.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == sample_attempt.id)
        )
        attempt = result.scalar_one()
        question_id = attempt.answers[0].question_id

        answers = [
            AttemptAnswerSave(question_id=question_id, selected_answer=AnswerOption.B)
        ]

        result = await service.save_progress(
            sample_attempt.id, test_student.id, answers
        )

        assert result is not None
        assert result.status == AttemptStatus.IN_PROGRESS
        # Verify answer was saved
        saved_answer = next(
            (a for a in result.answers if a.question_id == question_id), None
        )
        assert saved_answer is not None
        assert saved_answer.selected_answer == AnswerOption.B

    async def test_save_progress_multiple_answers(
        self, db_session: AsyncSession, sample_attempt: QuizAttempt, test_student: User
    ):
        """Test saving multiple answers."""
        service = AttemptService(db_session)

        # Get question IDs
        result = await db_session.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == sample_attempt.id)
        )
        attempt = result.scalar_one()

        answers = [
            AttemptAnswerSave(
                question_id=attempt.answers[0].question_id,
                selected_answer=AnswerOption.A,
            ),
            AttemptAnswerSave(
                question_id=attempt.answers[1].question_id,
                selected_answer=AnswerOption.B,
            ),
            AttemptAnswerSave(
                question_id=attempt.answers[2].question_id,
                selected_answer=AnswerOption.C,
            ),
        ]

        result = await service.save_progress(
            sample_attempt.id, test_student.id, answers
        )

        assert result is not None
        assert result.status == AttemptStatus.IN_PROGRESS

    async def test_save_progress_wrong_user(
        self,
        db_session: AsyncSession,
        sample_attempt: QuizAttempt,
        test_instructor: User,
    ):
        """Test saving progress for wrong user returns None."""
        service = AttemptService(db_session)

        answers = [
            AttemptAnswerSave(question_id=uuid4(), selected_answer=AnswerOption.A)
        ]

        result = await service.save_progress(
            sample_attempt.id, test_instructor.id, answers
        )

        assert result is None

    async def test_save_progress_nonexistent_attempt(
        self, db_session: AsyncSession, test_student: User
    ):
        """Test saving progress for non-existent attempt returns None."""
        service = AttemptService(db_session)

        answers = [
            AttemptAnswerSave(question_id=uuid4(), selected_answer=AnswerOption.A)
        ]

        result = await service.save_progress(uuid4(), test_student.id, answers)

        assert result is None


class TestAttemptServiceSubmit:
    """Tests for AttemptService.submit_attempt method."""

    async def test_submit_attempt_all_correct(
        self, db_session: AsyncSession, sample_quiz: Quiz, test_student: User
    ):
        """Test submitting an attempt with all correct answers."""
        # First, start an attempt
        service = AttemptService(db_session)
        attempt = await service.start_attempt(sample_quiz.id, test_student.id)

        # Load quiz questions
        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()

        # Build answers with all correct
        answers = [
            AttemptAnswerSave(question_id=q.id, selected_answer=q.correct_answer)
            for q in quiz.questions
        ]

        result = await service.submit_attempt(attempt.id, test_student.id, answers)

        assert result is not None
        assert result.status == AttemptStatus.COMPLETED
        assert result.score == 5  # All correct
        assert result.total_questions == 5
        assert result.completed_at is not None
        assert all(q.is_correct for q in result.questions)

    async def test_submit_attempt_partial_correct(
        self, db_session: AsyncSession, sample_quiz: Quiz, test_student: User
    ):
        """Test submitting an attempt with some correct answers."""
        service = AttemptService(db_session)
        attempt = await service.start_attempt(sample_quiz.id, test_student.id)

        # Load quiz questions
        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()
        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)

        # Build answers: first 3 correct, last 2 wrong
        answers = []
        for i, q in enumerate(sorted_questions):
            if i < 3:
                answers.append(
                    AttemptAnswerSave(
                        question_id=q.id, selected_answer=q.correct_answer
                    )
                )
            else:
                # Pick a wrong answer
                wrong = (
                    AnswerOption.A
                    if q.correct_answer != AnswerOption.A
                    else AnswerOption.B
                )
                answers.append(
                    AttemptAnswerSave(question_id=q.id, selected_answer=wrong)
                )

        result = await service.submit_attempt(attempt.id, test_student.id, answers)

        assert result is not None
        assert result.status == AttemptStatus.COMPLETED
        assert result.score == 3

    async def test_submit_attempt_all_wrong(
        self, db_session: AsyncSession, sample_quiz: Quiz, test_student: User
    ):
        """Test submitting an attempt with no correct answers."""
        service = AttemptService(db_session)
        attempt = await service.start_attempt(sample_quiz.id, test_student.id)

        # Load quiz questions
        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()

        # Build answers with all wrong
        answers = []
        for q in quiz.questions:
            wrong = (
                AnswerOption.A if q.correct_answer != AnswerOption.A else AnswerOption.B
            )
            answers.append(AttemptAnswerSave(question_id=q.id, selected_answer=wrong))

        result = await service.submit_attempt(attempt.id, test_student.id, answers)

        assert result is not None
        assert result.status == AttemptStatus.COMPLETED
        assert result.score == 0
        assert all(not q.is_correct for q in result.questions)

    async def test_submit_attempt_wrong_user(
        self,
        db_session: AsyncSession,
        sample_attempt: QuizAttempt,
        test_instructor: User,
    ):
        """Test submitting attempt for wrong user returns None."""
        service = AttemptService(db_session)

        answers = [
            AttemptAnswerSave(question_id=uuid4(), selected_answer=AnswerOption.A)
        ]

        result = await service.submit_attempt(
            sample_attempt.id, test_instructor.id, answers
        )

        assert result is None

    async def test_submit_already_completed_attempt(
        self,
        db_session: AsyncSession,
        completed_attempt: QuizAttempt,
        test_student: User,
    ):
        """Test submitting an already completed attempt returns None."""
        service = AttemptService(db_session)

        answers = [
            AttemptAnswerSave(question_id=uuid4(), selected_answer=AnswerOption.A)
        ]

        result = await service.submit_attempt(
            completed_attempt.id, test_student.id, answers
        )

        assert result is None


class TestAttemptServiceGetAttempt:
    """Tests for AttemptService.get_attempt method."""

    async def test_get_completed_attempt(
        self,
        db_session: AsyncSession,
        completed_attempt: QuizAttempt,
        test_student: User,
    ):
        """Test getting a completed attempt with results."""
        service = AttemptService(db_session)

        result = await service.get_attempt(completed_attempt.id, test_student.id)

        assert result is not None
        assert result.id == completed_attempt.id
        assert result.status == AttemptStatus.COMPLETED
        assert result.score == 4
        assert len(result.questions) == 5

    async def test_get_in_progress_attempt(
        self, db_session: AsyncSession, sample_attempt: QuizAttempt, test_student: User
    ):
        """Test getting an in-progress attempt."""
        service = AttemptService(db_session)

        result = await service.get_attempt(sample_attempt.id, test_student.id)

        assert result is not None
        assert result.id == sample_attempt.id
        assert result.status == AttemptStatus.IN_PROGRESS

    async def test_get_attempt_wrong_user(
        self,
        db_session: AsyncSession,
        sample_attempt: QuizAttempt,
        test_instructor: User,
    ):
        """Test getting attempt for wrong user returns None."""
        service = AttemptService(db_session)

        result = await service.get_attempt(sample_attempt.id, test_instructor.id)

        assert result is None

    async def test_get_nonexistent_attempt(
        self, db_session: AsyncSession, test_student: User
    ):
        """Test getting non-existent attempt returns None."""
        service = AttemptService(db_session)

        result = await service.get_attempt(uuid4(), test_student.id)

        assert result is None


class TestAttemptServiceGetUserAttempts:
    """Tests for AttemptService.get_user_attempts method."""

    async def test_get_user_attempts(
        self,
        db_session: AsyncSession,
        completed_attempt: QuizAttempt,
        test_student: User,
    ):
        """Test getting all attempts for a user."""
        service = AttemptService(db_session)

        result = await service.get_user_attempts(test_student.id)

        assert result is not None
        assert result.total >= 1
        assert any(a.id == completed_attempt.id for a in result.attempts)

    async def test_get_user_attempts_empty(
        self, db_session: AsyncSession, test_instructor: User
    ):
        """Test getting attempts for user with no attempts."""
        service = AttemptService(db_session)

        result = await service.get_user_attempts(test_instructor.id)

        assert result is not None
        assert result.total == 0
        assert len(result.attempts) == 0

    async def test_get_user_attempts_sorted_by_date(
        self, db_session: AsyncSession, sample_quiz: Quiz, test_student: User
    ):
        """Test that user attempts are sorted by date descending."""
        service = AttemptService(db_session)

        # Create multiple attempts
        attempt1 = await service.start_attempt(sample_quiz.id, test_student.id)
        # Complete it
        result_db = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result_db.scalar_one()
        answers = [
            AttemptAnswerSave(question_id=q.id, selected_answer=q.correct_answer)
            for q in quiz.questions
        ]
        await service.submit_attempt(attempt1.id, test_student.id, answers)

        # Start another attempt
        await service.start_attempt(sample_quiz.id, test_student.id)

        result = await service.get_user_attempts(test_student.id)

        assert result.total >= 2
        # Verify descending order
        if len(result.attempts) > 1:
            for i in range(len(result.attempts) - 1):
                assert (
                    result.attempts[i].started_at >= result.attempts[i + 1].started_at
                )
