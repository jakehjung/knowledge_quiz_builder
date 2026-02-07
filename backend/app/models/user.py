import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class ThemePreference(str, enum.Enum):
    BYU = "byu"
    UTAH = "utah"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    display_name = Column(String(255), nullable=True)
    theme_preference = Column(
        SQLEnum(ThemePreference, values_callable=lambda x: [e.value for e in x]),
        default=ThemePreference.BYU,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quizzes = relationship(
        "Quiz", back_populates="instructor", cascade="all, delete-orphan"
    )
    attempts = relationship(
        "QuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
