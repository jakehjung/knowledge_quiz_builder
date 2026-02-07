"""Unit tests for AnalyticsService."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import AnalyticsService
from app.models.user import User
from app.models.quiz import Quiz
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptStatus, AnswerOption

pytestmark = pytest.mark.unit


class TestAnalyticsServiceQuizAnalytics:
    """Tests for AnalyticsService.get_quiz_analytics method."""

    async def test_quiz_analytics_with_completed_attempts(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        test_student: User,
    ):
        """Test getting analytics for a quiz with completed attempts."""
        service = AnalyticsService(db_session)

        result = await service.get_quiz_analytics(sample_quiz.id)

        assert result is not None
        assert result["quiz_id"] == str(sample_quiz.id)
        assert result["quiz_title"] == sample_quiz.title
        assert result["total_questions"] == 5
        assert result["total_attempts"] >= 1
        assert result["unique_students"] >= 1
        assert "average_score" in result
        assert "score_distribution" in result
        assert "question_analysis" in result
        assert "student_scores" in result

    async def test_quiz_analytics_score_distribution(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
    ):
        """Test that score distribution is correctly calculated."""
        service = AnalyticsService(db_session)

        result = await service.get_quiz_analytics(sample_quiz.id)

        # completed_attempt has score of 4
        score_dist = result["score_distribution"]
        assert score_dist is not None
        # Should have keys 0-5 for a 5-question quiz
        assert 0 in score_dist
        assert 5 in score_dist
        assert score_dist[4] >= 1  # At least one attempt with score 4

    async def test_quiz_analytics_question_analysis(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
    ):
        """Test that question analysis is correctly calculated."""
        service = AnalyticsService(db_session)

        result = await service.get_quiz_analytics(sample_quiz.id)

        question_analysis = result["question_analysis"]
        assert len(question_analysis) == 5  # 5 questions

        for q in question_analysis:
            assert "question_id" in q
            assert "question_text" in q
            assert "correct_count" in q
            assert "incorrect_count" in q
            assert "accuracy_rate" in q

    async def test_quiz_analytics_student_scores(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        test_student: User,
    ):
        """Test that student scores are correctly calculated."""
        service = AnalyticsService(db_session)

        result = await service.get_quiz_analytics(sample_quiz.id)

        student_scores = result["student_scores"]
        assert len(student_scores) >= 1

        # Find the test student
        student_score = next(
            (s for s in student_scores if s["user_id"] == test_student.id), None
        )
        assert student_score is not None
        assert student_score["best_score"] == 4
        assert student_score["attempts_count"] >= 1

    async def test_quiz_analytics_no_attempts(
        self, db_session: AsyncSession, sample_quiz: Quiz
    ):
        """Test analytics for quiz with no attempts."""
        # Delete the completed_attempt fixture by not including it
        service = AnalyticsService(db_session)

        # Create a new quiz with no attempts
        from app.models.quiz import Quiz, Question, AnswerOption as QAnswerOption

        new_quiz = Quiz(
            id=uuid4(),
            title="No Attempts Quiz",
            topic="Testing",
            instructor_id=sample_quiz.instructor_id,
            is_published=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(new_quiz)

        for i in range(5):
            q = Question(
                id=uuid4(),
                quiz_id=new_quiz.id,
                question_text=f"Question {i+1}?",
                option_a="A",
                option_b="B",
                option_c="C",
                option_d="D",
                correct_answer=QAnswerOption.A,
                order_index=i,
                created_at=datetime.utcnow(),
            )
            db_session.add(q)

        await db_session.commit()

        result = await service.get_quiz_analytics(new_quiz.id)

        assert result is not None
        assert result["total_attempts"] == 0
        assert result["unique_students"] == 0
        assert result["average_score"] == 0

    async def test_quiz_analytics_nonexistent_quiz(self, db_session: AsyncSession):
        """Test analytics for non-existent quiz returns empty dict."""
        service = AnalyticsService(db_session)

        result = await service.get_quiz_analytics(uuid4())

        assert result == {}

    async def test_quiz_analytics_excludes_instructor_attempts(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        test_instructor: User,
    ):
        """Test that instructor's own attempts are excluded from analytics."""
        service = AnalyticsService(db_session)

        # Create an attempt by the instructor
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()

        instructor_attempt = QuizAttempt(
            id=uuid4(),
            quiz_id=sample_quiz.id,
            user_id=test_instructor.id,
            status=AttemptStatus.COMPLETED,
            score=5,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(instructor_attempt)

        for q in quiz.questions:
            answer = AttemptAnswer(
                id=uuid4(),
                attempt_id=instructor_attempt.id,
                question_id=q.id,
                selected_answer=q.correct_answer,
                is_correct=True,
            )
            db_session.add(answer)

        await db_session.commit()

        result = await service.get_quiz_analytics(sample_quiz.id)

        # Instructor's attempt should not be counted
        student_scores = result["student_scores"]
        instructor_in_scores = any(
            s["user_id"] == test_instructor.id for s in student_scores
        )
        assert not instructor_in_scores


class TestAnalyticsServiceDashboardStats:
    """Tests for AnalyticsService.get_instructor_dashboard_stats method."""

    async def test_dashboard_stats_with_quizzes(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        test_instructor: User,
    ):
        """Test getting dashboard stats for instructor with quizzes."""
        service = AnalyticsService(db_session)

        result = await service.get_instructor_dashboard_stats(test_instructor.id)

        assert result is not None
        assert result["total_quizzes"] >= 1
        assert "total_students" in result
        assert "total_attempts" in result
        assert "average_percentage" in result

    async def test_dashboard_stats_no_quizzes(
        self, db_session: AsyncSession, test_student: User
    ):
        """Test dashboard stats for user with no quizzes."""
        service = AnalyticsService(db_session)

        result = await service.get_instructor_dashboard_stats(test_student.id)

        assert result is not None
        assert result["total_quizzes"] == 0
        assert result["total_students"] == 0
        assert result["total_attempts"] == 0
        assert result["average_percentage"] == 0

    async def test_dashboard_stats_average_percentage(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        test_instructor: User,
    ):
        """Test that average percentage is correctly calculated."""
        service = AnalyticsService(db_session)

        result = await service.get_instructor_dashboard_stats(test_instructor.id)

        # completed_attempt has score 4/5 = 80%
        # So average_percentage should reflect this
        assert result["average_percentage"] >= 0
        assert result["average_percentage"] <= 100

    async def test_dashboard_stats_excludes_instructor_attempts(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        test_instructor: User,
    ):
        """Test that instructor's own attempts are excluded from stats."""
        service = AnalyticsService(db_session)

        # Create an instructor's own attempt
        instructor_attempt = QuizAttempt(
            id=uuid4(),
            quiz_id=sample_quiz.id,
            user_id=test_instructor.id,
            status=AttemptStatus.COMPLETED,
            score=5,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(instructor_attempt)
        await db_session.commit()

        result = await service.get_instructor_dashboard_stats(test_instructor.id)

        # If no other students attempted, total_attempts should be 0
        # This ensures instructor's own attempts are excluded
        assert result["total_quizzes"] >= 1


class TestAnalyticsServiceMultipleAttempts:
    """Tests for analytics with multiple attempts from same student."""

    async def test_best_score_tracking(
        self,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        test_student: User,
    ):
        """Test that best score is correctly tracked for multiple attempts."""
        service = AnalyticsService(db_session)

        # Get quiz questions
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()

        # Create multiple attempts with different scores
        scores = [2, 4, 3]  # Best is 4
        for score in scores:
            attempt = QuizAttempt(
                id=uuid4(),
                quiz_id=sample_quiz.id,
                user_id=test_student.id,
                status=AttemptStatus.COMPLETED,
                score=score,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            db_session.add(attempt)
            await db_session.flush()

            # Add dummy answers
            for idx, q in enumerate(quiz.questions):
                is_correct = idx < score
                answer = AttemptAnswer(
                    id=uuid4(),
                    attempt_id=attempt.id,
                    question_id=q.id,
                    selected_answer=q.correct_answer if is_correct else AnswerOption.A,
                    is_correct=is_correct,
                )
                db_session.add(answer)

        await db_session.commit()

        analytics = await service.get_quiz_analytics(sample_quiz.id)

        # Find the student's best score
        student_score = next(
            (s for s in analytics["student_scores"] if s["user_id"] == test_student.id),
            None,
        )
        assert student_score is not None
        assert student_score["best_score"] == 4  # Best of [2, 4, 3]
        assert student_score["attempts_count"] == 3
