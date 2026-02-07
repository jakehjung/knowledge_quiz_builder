"""Core test fixtures for the Knowledge Quiz Builder."""

import pytest
from datetime import datetime
from uuid import uuid4
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole, ThemePreference
from app.models.quiz import Quiz, Question, QuizTag, AnswerOption
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptStatus
from app.models.token import RefreshToken
from app.utils.auth import (
    hash_password,
    create_access_token,
    create_refresh_token,
)

# SQLite async engine for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Register UUID type adapter for SQLite
SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "VARCHAR(36)"


@pytest.fixture
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database session for each test."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_app(db_session: AsyncSession):
    """FastAPI app with test database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def instructor_password() -> str:
    """Plain text password for test instructor."""
    return "TestPass123!"


@pytest.fixture
def student_password() -> str:
    """Plain text password for test student."""
    return "Student456@"


@pytest.fixture
async def test_instructor(db_session: AsyncSession, instructor_password: str) -> User:
    """Create a test instructor user."""
    user = User(
        id=uuid4(),
        email="instructor@test.com",
        password_hash=hash_password(instructor_password),
        role=UserRole.INSTRUCTOR,
        display_name="Test Instructor",
        theme_preference=ThemePreference.BYU,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_student(db_session: AsyncSession, student_password: str) -> User:
    """Create a test student user."""
    user = User(
        id=uuid4(),
        email="student@test.com",
        password_hash=hash_password(student_password),
        role=UserRole.STUDENT,
        display_name="Test Student",
        theme_preference=ThemePreference.UTAH,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def instructor_token(test_instructor: User) -> str:
    """JWT access token for test instructor."""
    return create_access_token(test_instructor.id, test_instructor.role.value)


@pytest.fixture
def student_token(test_student: User) -> str:
    """JWT access token for test student."""
    return create_access_token(test_student.id, test_student.role.value)


@pytest.fixture
def instructor_auth_headers(instructor_token: str) -> Dict[str, str]:
    """HTTP headers with instructor authorization."""
    return {"Authorization": f"Bearer {instructor_token}"}


@pytest.fixture
def student_auth_headers(student_token: str) -> Dict[str, str]:
    """HTTP headers with student authorization."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
async def instructor_refresh_token(
    db_session: AsyncSession, test_instructor: User
) -> str:
    """Create and store a refresh token for the instructor."""
    refresh_token, token_hash, expires_at = create_refresh_token(test_instructor.id)

    token_obj = RefreshToken(
        user_id=test_instructor.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db_session.add(token_obj)
    await db_session.commit()

    return refresh_token


@pytest.fixture
def sample_question_data() -> list[Dict[str, Any]]:
    """Sample question data for quiz creation."""
    return [
        {
            "question_text": "What is the capital of France?",
            "option_a": "London",
            "option_b": "Paris",
            "option_c": "Berlin",
            "option_d": "Madrid",
            "correct_answer": "B",
            "explanation": "Paris is the capital and largest city of France.",
        },
        {
            "question_text": "What is 2 + 2?",
            "option_a": "3",
            "option_b": "4",
            "option_c": "5",
            "option_d": "6",
            "correct_answer": "B",
            "explanation": "Basic arithmetic: 2 + 2 = 4.",
        },
        {
            "question_text": "Which planet is known as the Red Planet?",
            "option_a": "Venus",
            "option_b": "Jupiter",
            "option_c": "Mars",
            "option_d": "Saturn",
            "correct_answer": "C",
            "explanation": "Mars appears red due to iron oxide on its surface.",
        },
        {
            "question_text": "What is the chemical symbol for water?",
            "option_a": "O2",
            "option_b": "CO2",
            "option_c": "H2O",
            "option_d": "NaCl",
            "correct_answer": "C",
            "explanation": "Water is composed of two hydrogen atoms and one oxygen atom.",
        },
        {
            "question_text": "Who painted the Mona Lisa?",
            "option_a": "Vincent van Gogh",
            "option_b": "Leonardo da Vinci",
            "option_c": "Pablo Picasso",
            "option_d": "Michelangelo",
            "correct_answer": "B",
            "explanation": "Leonardo da Vinci painted the Mona Lisa between 1503-1519.",
        },
    ]


@pytest.fixture
async def sample_quiz(
    db_session: AsyncSession,
    test_instructor: User,
    sample_question_data: list[Dict[str, Any]],
) -> Quiz:
    """Create a sample quiz with 5 questions."""
    quiz = Quiz(
        id=uuid4(),
        title="Sample Test Quiz",
        description="A quiz for testing purposes",
        topic="General Knowledge",
        instructor_id=test_instructor.id,
        is_published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(quiz)
    await db_session.flush()

    # Add tags
    for tag_name in ["test", "general", "knowledge"]:
        tag = QuizTag(quiz_id=quiz.id, tag=tag_name)
        db_session.add(tag)

    # Add questions
    for idx, q_data in enumerate(sample_question_data):
        question = Question(
            id=uuid4(),
            quiz_id=quiz.id,
            question_text=q_data["question_text"],
            option_a=q_data["option_a"],
            option_b=q_data["option_b"],
            option_c=q_data["option_c"],
            option_d=q_data["option_d"],
            correct_answer=AnswerOption(q_data["correct_answer"]),
            explanation=q_data["explanation"],
            order_index=idx,
            created_at=datetime.utcnow(),
        )
        db_session.add(question)

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest.fixture
async def sample_attempt(
    db_session: AsyncSession,
    sample_quiz: Quiz,
    test_student: User,
) -> QuizAttempt:
    """Create a sample in-progress quiz attempt."""
    attempt = QuizAttempt(
        id=uuid4(),
        quiz_id=sample_quiz.id,
        user_id=test_student.id,
        status=AttemptStatus.IN_PROGRESS,
        started_at=datetime.utcnow(),
    )
    db_session.add(attempt)
    await db_session.flush()

    # Get quiz questions (need to load them)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == sample_quiz.id)
    )
    quiz = result.scalar_one()

    # Create empty answer slots
    for question in quiz.questions:
        answer = AttemptAnswer(
            id=uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
            selected_answer=None,
            is_correct=None,
        )
        db_session.add(answer)

    await db_session.commit()
    await db_session.refresh(attempt)
    return attempt


@pytest.fixture
async def completed_attempt(
    db_session: AsyncSession,
    sample_quiz: Quiz,
    test_student: User,
) -> QuizAttempt:
    """Create a completed quiz attempt with score."""
    attempt = QuizAttempt(
        id=uuid4(),
        quiz_id=sample_quiz.id,
        user_id=test_student.id,
        status=AttemptStatus.COMPLETED,
        score=4,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db_session.add(attempt)
    await db_session.flush()

    # Get quiz questions
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == sample_quiz.id)
    )
    quiz = result.scalar_one()

    # Create answered slots (4 correct, 1 incorrect)
    for idx, question in enumerate(sorted(quiz.questions, key=lambda q: q.order_index)):
        is_correct = idx < 4  # First 4 are correct
        answer = AttemptAnswer(
            id=uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
            selected_answer=question.correct_answer if is_correct else AnswerOption.A,
            is_correct=is_correct,
        )
        db_session.add(answer)

    await db_session.commit()
    await db_session.refresh(attempt)
    return attempt


@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response for quiz generation."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I've created a quiz about Python programming for you!",
                    "tool_calls": [
                        {
                            "id": "call_test123",
                            "type": "function",
                            "function": {
                                "name": "generate_quiz",
                                "arguments": '{"topic": "Python Programming", "tags": ["python", "programming"]}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


@pytest.fixture
def quiz_create_data(sample_question_data: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Data for creating a quiz via API."""
    return {
        "title": "API Test Quiz",
        "description": "Created via API test",
        "topic": "Testing",
        "tags": ["api", "test"],
        "questions": sample_question_data,
    }
