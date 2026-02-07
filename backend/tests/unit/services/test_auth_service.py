"""Unit tests for AuthService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.user import User, UserRole

pytestmark = pytest.mark.unit


class TestAuthServiceRegister:
    """Tests for AuthService.register method."""

    async def test_register_new_instructor(self, db_session: AsyncSession):
        """Test successful instructor registration."""
        service = AuthService(db_session)
        user_data = UserCreate(
            email="newinstructor@test.com",
            password="SecurePass123!",
            role=UserRole.INSTRUCTOR,
            display_name="New Instructor",
        )

        result = await service.register(user_data)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.email == "newinstructor@test.com"
        assert result.user.role == UserRole.INSTRUCTOR
        assert result.user.display_name == "New Instructor"

    async def test_register_new_student(self, db_session: AsyncSession):
        """Test successful student registration."""
        service = AuthService(db_session)
        user_data = UserCreate(
            email="newstudent@test.com",
            password="SecurePass456@",
            role=UserRole.STUDENT,
        )

        result = await service.register(user_data)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.email == "newstudent@test.com"
        assert result.user.role == UserRole.STUDENT

    async def test_register_duplicate_email_fails(
        self, db_session: AsyncSession, test_instructor: User
    ):
        """Test that registering with existing email fails."""
        service = AuthService(db_session)
        user_data = UserCreate(
            email=test_instructor.email,
            password="AnotherPass789#",
            role=UserRole.STUDENT,
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await service.register(user_data)

    async def test_register_without_display_name(self, db_session: AsyncSession):
        """Test registration without providing display name."""
        service = AuthService(db_session)
        user_data = UserCreate(
            email="nodisplayname@test.com",
            password="SecurePass123!",
            role=UserRole.STUDENT,
        )

        result = await service.register(user_data)

        assert result.user.display_name is None


class TestAuthServiceLogin:
    """Tests for AuthService.login method."""

    async def test_login_valid_credentials(
        self, db_session: AsyncSession, test_instructor: User, instructor_password: str
    ):
        """Test successful login with valid credentials."""
        service = AuthService(db_session)

        result = await service.login(test_instructor.email, instructor_password)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.email == test_instructor.email

    async def test_login_invalid_email(self, db_session: AsyncSession):
        """Test login with non-existent email."""
        service = AuthService(db_session)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login("nonexistent@test.com", "SomePassword123!")

    async def test_login_invalid_password(
        self, db_session: AsyncSession, test_instructor: User
    ):
        """Test login with wrong password."""
        service = AuthService(db_session)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(test_instructor.email, "WrongPassword123!")


class TestAuthServiceRefresh:
    """Tests for AuthService.refresh_access_token method."""

    async def test_refresh_valid_token(
        self, db_session: AsyncSession, instructor_refresh_token: str
    ):
        """Test refreshing access token with valid refresh token."""
        service = AuthService(db_session)

        result = await service.refresh_access_token(instructor_refresh_token)

        assert "access_token" in result
        assert result["access_token"] is not None

    async def test_refresh_invalid_token(self, db_session: AsyncSession):
        """Test refreshing with invalid refresh token."""
        service = AuthService(db_session)

        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await service.refresh_access_token("invalid-token")


class TestAuthServiceLogout:
    """Tests for AuthService.logout method."""

    async def test_logout_valid_token(
        self, db_session: AsyncSession, instructor_refresh_token: str
    ):
        """Test logout with valid refresh token."""
        service = AuthService(db_session)

        # Logout should not raise
        await service.logout(instructor_refresh_token)

        # Token should be invalidated - refresh should fail
        with pytest.raises(ValueError, match="Invalid or expired refresh token"):
            await service.refresh_access_token(instructor_refresh_token)

    async def test_logout_invalid_token(self, db_session: AsyncSession):
        """Test logout with non-existent token (should not raise)."""
        service = AuthService(db_session)

        # Should not raise even with invalid token
        await service.logout("nonexistent-token")


class TestAuthServiceGetUser:
    """Tests for AuthService.get_user_by_id method."""

    async def test_get_existing_user(
        self, db_session: AsyncSession, test_instructor: User
    ):
        """Test getting an existing user by ID."""
        service = AuthService(db_session)

        result = await service.get_user_by_id(test_instructor.id)

        assert result is not None
        assert result.id == test_instructor.id
        assert result.email == test_instructor.email

    async def test_get_nonexistent_user(self, db_session: AsyncSession):
        """Test getting a non-existent user returns None."""
        from uuid import uuid4

        service = AuthService(db_session)

        result = await service.get_user_by_id(uuid4())

        assert result is None
