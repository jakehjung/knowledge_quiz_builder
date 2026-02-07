"""Integration tests for quiz routes."""

import pytest
from typing import Dict, Any
from httpx import AsyncClient

from app.models.user import User
from app.models.quiz import Quiz
from app.models.attempt import QuizAttempt

pytestmark = pytest.mark.integration


class TestListQuizzesEndpoint:
    """Tests for GET /api/quizzes."""

    async def test_list_quizzes_public(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test listing quizzes without authentication."""
        response = await test_client.get("/api/quizzes")

        assert response.status_code == 200
        data = response.json()
        assert "quizzes" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_list_quizzes_with_search(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test listing quizzes with search parameter."""
        response = await test_client.get("/api/quizzes?search=Sample")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_list_quizzes_with_tags(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test listing quizzes filtered by tags."""
        response = await test_client.get("/api/quizzes?tags=test")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_list_quizzes_with_sort(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test listing quizzes with different sort orders."""
        for sort in ["newest", "oldest", "alphabetical", "popular"]:
            response = await test_client.get(f"/api/quizzes?sort={sort}")
            assert response.status_code == 200

    async def test_list_quizzes_pagination(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test listing quizzes with pagination."""
        response = await test_client.get("/api/quizzes?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestGetMyQuizzesEndpoint:
    """Tests for GET /api/quizzes/my."""

    async def test_get_my_quizzes_instructor(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        test_instructor: User,
        instructor_auth_headers: dict,
    ):
        """Test getting instructor's own quizzes."""
        response = await test_client.get(
            "/api/quizzes/my",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(
            q["instructor"]["id"] == str(test_instructor.id) for q in data["quizzes"]
        )

    async def test_get_my_quizzes_student_forbidden(
        self, test_client: AsyncClient, student_auth_headers: dict
    ):
        """Test that students cannot access my quizzes endpoint."""
        response = await test_client.get(
            "/api/quizzes/my",
            headers=student_auth_headers,
        )

        assert response.status_code == 403

    async def test_get_my_quizzes_unauthenticated(self, test_client: AsyncClient):
        """Test that unauthenticated users cannot access my quizzes."""
        response = await test_client.get("/api/quizzes/my")

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]


class TestGetMyStatsEndpoint:
    """Tests for GET /api/quizzes/my/stats."""

    async def test_get_my_stats_instructor(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        instructor_auth_headers: dict,
    ):
        """Test getting instructor's dashboard stats."""
        response = await test_client.get(
            "/api/quizzes/my/stats",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_quizzes" in data
        assert "total_students" in data
        assert "total_attempts" in data
        assert "average_percentage" in data

    async def test_get_my_stats_student_forbidden(
        self, test_client: AsyncClient, student_auth_headers: dict
    ):
        """Test that students cannot access stats endpoint."""
        response = await test_client.get(
            "/api/quizzes/my/stats",
            headers=student_auth_headers,
        )

        assert response.status_code == 403


class TestGetQuizEndpoint:
    """Tests for GET /api/quizzes/{quiz_id}."""

    async def test_get_quiz_instructor_view(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        instructor_auth_headers: dict,
    ):
        """Test instructor sees full quiz details."""
        response = await test_client.get(
            f"/api/quizzes/{sample_quiz.id}",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_quiz.id)
        assert "questions" in data
        # Instructor should see correct answers
        assert all("correct_answer" in q for q in data["questions"])

    async def test_get_quiz_student_view(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test student sees quiz without answers."""
        response = await test_client.get(
            f"/api/quizzes/{sample_quiz.id}",
            headers=student_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_quiz.id)
        # Student should NOT see correct answers
        assert all("correct_answer" not in q for q in data["questions"])

    async def test_get_quiz_not_found(
        self, test_client: AsyncClient, instructor_auth_headers: dict
    ):
        """Test getting non-existent quiz."""
        from uuid import uuid4

        response = await test_client.get(
            f"/api/quizzes/{uuid4()}",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404

    async def test_get_quiz_unauthenticated(
        self, test_client: AsyncClient, sample_quiz: Quiz
    ):
        """Test getting quiz without authentication."""
        response = await test_client.get(f"/api/quizzes/{sample_quiz.id}")

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]


class TestCreateQuizEndpoint:
    """Tests for POST /api/quizzes."""

    async def test_create_quiz_success(
        self,
        test_client: AsyncClient,
        instructor_auth_headers: dict,
        quiz_create_data: Dict[str, Any],
    ):
        """Test successful quiz creation."""
        response = await test_client.post(
            "/api/quizzes",
            json=quiz_create_data,
            headers=instructor_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == quiz_create_data["title"]
        assert data["topic"] == quiz_create_data["topic"]
        assert len(data["questions"]) == 5

    async def test_create_quiz_student_forbidden(
        self,
        test_client: AsyncClient,
        student_auth_headers: dict,
        quiz_create_data: Dict[str, Any],
    ):
        """Test that students cannot create quizzes."""
        response = await test_client.post(
            "/api/quizzes",
            json=quiz_create_data,
            headers=student_auth_headers,
        )

        assert response.status_code == 403

    async def test_create_quiz_unauthenticated(
        self, test_client: AsyncClient, quiz_create_data: Dict[str, Any]
    ):
        """Test creating quiz without authentication."""
        response = await test_client.post(
            "/api/quizzes",
            json=quiz_create_data,
        )

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]

    async def test_create_quiz_missing_fields(
        self, test_client: AsyncClient, instructor_auth_headers: dict
    ):
        """Test creating quiz with missing required fields."""
        response = await test_client.post(
            "/api/quizzes",
            json={"title": "Only Title"},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 422


class TestUpdateQuizEndpoint:
    """Tests for PUT /api/quizzes/{quiz_id}."""

    async def test_update_quiz_title(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        instructor_auth_headers: dict,
    ):
        """Test updating quiz title."""
        response = await test_client.put(
            f"/api/quizzes/{sample_quiz.id}",
            json={"title": "Updated Title"},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.skip(
        reason="SQLite test session caching issue - works with PostgreSQL"
    )
    async def test_update_quiz_tags(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        instructor_auth_headers: dict,
    ):
        """Test updating quiz tags."""
        response = await test_client.put(
            f"/api/quizzes/{sample_quiz.id}",
            json={"tags": ["updated", "tags"]},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        # Re-fetch to verify tags were updated
        get_response = await test_client.get(
            f"/api/quizzes/{sample_quiz.id}",
            headers=instructor_auth_headers,
        )
        data = get_response.json()
        assert set(data["tags"]) == {"updated", "tags"}

    async def test_update_quiz_wrong_instructor(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test that non-owner cannot update quiz."""
        # Note: student can't update any quiz as they're not instructor
        response = await test_client.put(
            f"/api/quizzes/{sample_quiz.id}",
            json={"title": "Should Fail"},
            headers=student_auth_headers,
        )

        assert response.status_code == 403

    async def test_update_quiz_not_found(
        self, test_client: AsyncClient, instructor_auth_headers: dict
    ):
        """Test updating non-existent quiz."""
        from uuid import uuid4

        response = await test_client.put(
            f"/api/quizzes/{uuid4()}",
            json={"title": "Should Fail"},
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404


class TestDeleteQuizEndpoint:
    """Tests for DELETE /api/quizzes/{quiz_id}."""

    async def test_delete_quiz_success(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        instructor_auth_headers: dict,
    ):
        """Test successful quiz deletion."""
        quiz_id = sample_quiz.id
        response = await test_client.delete(
            f"/api/quizzes/{quiz_id}",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await test_client.get(
            f"/api/quizzes/{quiz_id}",
            headers=instructor_auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_quiz_wrong_instructor(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test that non-owner cannot delete quiz."""
        response = await test_client.delete(
            f"/api/quizzes/{sample_quiz.id}",
            headers=student_auth_headers,
        )

        assert response.status_code == 403

    async def test_delete_quiz_not_found(
        self, test_client: AsyncClient, instructor_auth_headers: dict
    ):
        """Test deleting non-existent quiz."""
        from uuid import uuid4

        response = await test_client.delete(
            f"/api/quizzes/{uuid4()}",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404


class TestGetQuizAnalyticsEndpoint:
    """Tests for GET /api/quizzes/{quiz_id}/analytics."""

    async def test_get_analytics_success(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        completed_attempt: QuizAttempt,
        instructor_auth_headers: dict,
    ):
        """Test getting quiz analytics."""
        response = await test_client.get(
            f"/api/quizzes/{sample_quiz.id}/analytics",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quiz_id"] == str(sample_quiz.id)
        assert "total_attempts" in data
        assert "unique_students" in data
        assert "average_score" in data
        assert "score_distribution" in data
        assert "question_analysis" in data
        assert "student_scores" in data

    async def test_get_analytics_wrong_instructor(
        self,
        test_client: AsyncClient,
        sample_quiz: Quiz,
        student_auth_headers: dict,
    ):
        """Test that non-owner cannot view analytics."""
        response = await test_client.get(
            f"/api/quizzes/{sample_quiz.id}/analytics",
            headers=student_auth_headers,
        )

        assert response.status_code == 403

    async def test_get_analytics_not_found(
        self, test_client: AsyncClient, instructor_auth_headers: dict
    ):
        """Test getting analytics for non-existent quiz."""
        from uuid import uuid4

        response = await test_client.get(
            f"/api/quizzes/{uuid4()}/analytics",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 404
