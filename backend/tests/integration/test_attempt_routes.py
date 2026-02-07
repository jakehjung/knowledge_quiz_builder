"""Integration tests for quiz attempt routes."""

import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz
from app.models.attempt import QuizAttempt

pytestmark = pytest.mark.integration


class TestStartAttemptEndpoint:
    """Tests for POST /api/attempts/{quiz_id}/start."""

    async def test_start_attempt_success(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test starting a new quiz attempt."""
        response = await test_client.post(
            f"/api/attempts/{sample_quiz.id}/start",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quiz_id"] == str(sample_quiz.id)
        assert data["status"] == "in_progress"
        assert "answers" in data
        assert len(data["answers"]) == 5

    async def test_start_attempt_resumes_existing(
        self,
        test_client: AsyncClient,
        sample_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test that starting returns existing in-progress attempt."""
        response = await test_client.post(
            f"/api/attempts/{sample_attempt.quiz_id}/start",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_attempt.id)

    async def test_start_attempt_quiz_not_found(
        self,
        test_client: AsyncClient,
        student_auth_headers: dict,
    ):
        """Test starting attempt for non-existent quiz."""
        response = await test_client.post(
            f"/api/attempts/{uuid4()}/start",
            headers=student_auth_headers,
        )

        assert response.status_code == 404

    async def test_start_attempt_unauthenticated(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
    ):
        """Test starting attempt without authentication."""
        response = await test_client.post(f"/api/attempts/{sample_quiz.id}/start")

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]


class TestSaveProgressEndpoint:
    """Tests for PUT /api/attempts/{attempt_id}."""

    async def test_save_progress_success(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        sample_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test saving quiz progress."""
        # Get question IDs
        result = await db_session.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers))
            .where(QuizAttempt.id == sample_attempt.id)
        )
        attempt = result.scalar_one()
        question_id = str(attempt.answers[0].question_id)

        response = await test_client.put(
            f"/api/attempts/{sample_attempt.id}",
            json={"answers": [{"question_id": question_id, "selected_answer": "B"}]},
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_save_progress_wrong_user(
        self,
        test_client: AsyncClient,
        sample_attempt: QuizAttempt,
        instructor_auth_headers: dict,
    ):
        """Test saving progress for wrong user."""
        response = await test_client.put(
            f"/api/attempts/{sample_attempt.id}",
            json={"answers": []},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404

    async def test_save_progress_attempt_not_found(
        self,
        test_client: AsyncClient,
        student_auth_headers: dict,
    ):
        """Test saving progress for non-existent attempt."""
        response = await test_client.put(
            f"/api/attempts/{uuid4()}",
            json={"answers": []},
            headers=student_auth_headers,
        )

        assert response.status_code == 404


class TestSubmitAttemptEndpoint:
    """Tests for POST /api/attempts/{attempt_id}/submit."""

    async def test_submit_attempt_success(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test submitting a quiz attempt."""
        # Start an attempt first
        start_response = await test_client.post(
            f"/api/attempts/{sample_quiz.id}/start",
            headers=student_auth_headers,
        )
        attempt_id = start_response.json()["id"]

        # Get quiz questions to build answers
        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()

        # Submit with all correct answers
        answers = [
            {"question_id": str(q.id), "selected_answer": q.correct_answer.value}
            for q in quiz.questions
        ]

        response = await test_client.post(
            f"/api/attempts/{attempt_id}/submit",
            json={"answers": answers},
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["score"] == 5
        assert data["total_questions"] == 5

    async def test_submit_attempt_partial_score(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test submitting with partial correct answers."""
        # Start an attempt
        start_response = await test_client.post(
            f"/api/attempts/{sample_quiz.id}/start",
            headers=student_auth_headers,
        )
        attempt_id = start_response.json()["id"]

        # Get quiz questions
        result = await db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == sample_quiz.id)
        )
        quiz = result.scalar_one()
        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)

        # Submit with 3 correct, 2 wrong
        answers = []
        for i, q in enumerate(sorted_questions):
            if i < 3:
                answers.append(
                    {
                        "question_id": str(q.id),
                        "selected_answer": q.correct_answer.value,
                    }
                )
            else:
                wrong = "A" if q.correct_answer.value != "A" else "B"
                answers.append({"question_id": str(q.id), "selected_answer": wrong})

        response = await test_client.post(
            f"/api/attempts/{attempt_id}/submit",
            json={"answers": answers},
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 3

    async def test_submit_attempt_wrong_user(
        self,
        test_client: AsyncClient,
        sample_attempt: QuizAttempt,
        instructor_auth_headers: dict,
    ):
        """Test submitting attempt for wrong user."""
        response = await test_client.post(
            f"/api/attempts/{sample_attempt.id}/submit",
            json={"answers": []},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404

    async def test_submit_already_completed(
        self,
        test_client: AsyncClient,
        completed_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test submitting already completed attempt."""
        response = await test_client.post(
            f"/api/attempts/{completed_attempt.id}/submit",
            json={"answers": []},
            headers=student_auth_headers,
        )

        assert response.status_code == 404


class TestGetMyAttemptsEndpoint:
    """Tests for GET /api/attempts/my."""

    async def test_get_my_attempts_success(
        self,
        test_client: AsyncClient,
        completed_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test getting user's attempts."""
        response = await test_client.get(
            "/api/attempts/my",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "attempts" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_my_attempts_empty(
        self,
        test_client: AsyncClient,
        instructor_auth_headers: dict,
    ):
        """Test getting attempts for user with no attempts."""
        response = await test_client.get(
            "/api/attempts/my",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_get_my_attempts_unauthenticated(
        self,
        test_client: AsyncClient,
    ):
        """Test getting attempts without authentication."""
        response = await test_client.get("/api/attempts/my")

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]


class TestGetAttemptEndpoint:
    """Tests for GET /api/attempts/{attempt_id}."""

    async def test_get_completed_attempt(
        self,
        test_client: AsyncClient,
        completed_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test getting a completed attempt."""
        response = await test_client.get(
            f"/api/attempts/{completed_attempt.id}",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(completed_attempt.id)
        assert data["status"] == "completed"
        assert data["score"] == 4
        assert "questions" in data

    async def test_get_in_progress_attempt(
        self,
        test_client: AsyncClient,
        sample_attempt: QuizAttempt,
        student_auth_headers: dict,
    ):
        """Test getting an in-progress attempt."""
        response = await test_client.get(
            f"/api/attempts/{sample_attempt.id}",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_get_attempt_wrong_user(
        self,
        test_client: AsyncClient,
        sample_attempt: QuizAttempt,
        instructor_auth_headers: dict,
    ):
        """Test getting attempt for wrong user."""
        response = await test_client.get(
            f"/api/attempts/{sample_attempt.id}",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404

    async def test_get_attempt_not_found(
        self,
        test_client: AsyncClient,
        student_auth_headers: dict,
    ):
        """Test getting non-existent attempt."""
        response = await test_client.get(
            f"/api/attempts/{uuid4()}",
            headers=student_auth_headers,
        )

        assert response.status_code == 404
