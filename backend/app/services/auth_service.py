from datetime import datetime
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.token import RefreshToken
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> TokenResponse:
        # Check if user exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            display_name=user_data.display_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, token_hash, expires_at = create_refresh_token(user.id)

        # Store refresh token
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Generate tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, token_hash, expires_at = create_refresh_token(user.id)

        # Store refresh token
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def refresh_access_token(self, refresh_token: str) -> dict:
        token_hash = hash_token(refresh_token)

        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.expires_at > datetime.utcnow())
        )
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            raise ValueError("Invalid or expired refresh token")

        # Get user
        result = await self.db.execute(select(User).where(User.id == token_obj.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Generate new access token
        access_token = create_access_token(user.id, user.role.value)

        return {"access_token": access_token}

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        await self.db.execute(
            delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        await self.db.commit()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
