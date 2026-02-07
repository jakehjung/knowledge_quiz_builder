"""Integration tests for authentication routes."""

import pytest
from httpx import AsyncClient

from app.models.user import User

pytestmark = pytest.mark.integration


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register."""

    async def test_register_instructor_success(self, test_client: AsyncClient):
        """Test successful instructor registration."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "newinstructor@test.com",
                "password": "SecurePass123!",
                "role": "instructor",
                "display_name": "New Instructor",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newinstructor@test.com"
        assert data["user"]["role"] == "instructor"
        assert data["user"]["display_name"] == "New Instructor"

    async def test_register_student_success(self, test_client: AsyncClient):
        """Test successful student registration."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "newstudent@test.com",
                "password": "SecurePass456@",
                "role": "student",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newstudent@test.com"
        assert data["user"]["role"] == "student"

    async def test_register_duplicate_email(
        self, test_client: AsyncClient, test_instructor: User
    ):
        """Test registration with existing email fails."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": test_instructor.email,
                "password": "AnotherPass123!",
                "role": "student",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_weak_password(self, test_client: AsyncClient):
        """Test registration with weak password fails validation."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "weakpass@test.com",
                "password": "short",
                "role": "student",
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_register_invalid_email(self, test_client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "role": "student",
            },
        )

        assert response.status_code == 422

    async def test_register_invalid_role(self, test_client: AsyncClient):
        """Test registration with invalid role fails."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "email": "invalidrole@test.com",
                "password": "SecurePass123!",
                "role": "admin",  # Invalid role
            },
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /api/auth/login."""

    async def test_login_success(
        self, test_client: AsyncClient, test_instructor: User, instructor_password: str
    ):
        """Test successful login."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": test_instructor.email,
                "password": instructor_password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_instructor.email

    async def test_login_wrong_password(
        self, test_client: AsyncClient, test_instructor: User
    ):
        """Test login with wrong password fails."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": test_instructor.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_email(self, test_client: AsyncClient):
        """Test login with non-existent email fails."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 401

    async def test_login_missing_fields(self, test_client: AsyncClient):
        """Test login with missing fields fails."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "test@test.com",
            },
        )

        assert response.status_code == 422


class TestRefreshEndpoint:
    """Tests for POST /api/auth/refresh."""

    async def test_refresh_success(
        self, test_client: AsyncClient, instructor_refresh_token: str
    ):
        """Test successful token refresh."""
        response = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": instructor_refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_invalid_token(self, test_client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout."""

    async def test_logout_success(
        self, test_client: AsyncClient, instructor_refresh_token: str
    ):
        """Test successful logout."""
        response = await test_client.post(
            "/api/auth/logout",
            json={"refresh_token": instructor_refresh_token},
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    async def test_logout_invalid_token(self, test_client: AsyncClient):
        """Test logout with invalid token still succeeds (idempotent)."""
        response = await test_client.post(
            "/api/auth/logout",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 200


class TestMeEndpoint:
    """Tests for GET /api/auth/me."""

    async def test_me_authenticated(
        self,
        test_client: AsyncClient,
        test_instructor: User,
        instructor_auth_headers: dict,
    ):
        """Test getting current user when authenticated."""
        response = await test_client.get(
            "/api/auth/me",
            headers=instructor_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_instructor.email
        assert data["role"] == test_instructor.role.value

    async def test_me_unauthenticated(self, test_client: AsyncClient):
        """Test getting current user without auth fails."""
        response = await test_client.get("/api/auth/me")

        # API returns 403 Forbidden for missing auth
        assert response.status_code in [401, 403]

    async def test_me_invalid_token(self, test_client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
