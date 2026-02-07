"""Benchmark-specific fixtures for AI quality tests."""

import os
import pytest
from typing import Optional

from openai import AsyncOpenAI


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment."""
    return os.environ.get("OPENAI_API_KEY")


@pytest.fixture
def openai_api_key() -> str:
    """Get OpenAI API key, skip test if not available."""
    key = get_openai_api_key()
    if not key:
        pytest.skip("OPENAI_API_KEY not set - skipping AI benchmark test")
    return key


@pytest.fixture
async def openai_client(openai_api_key: str) -> AsyncOpenAI:
    """Create OpenAI client for benchmark tests."""
    return AsyncOpenAI(api_key=openai_api_key)


@pytest.fixture
def quiz_generation_topics() -> list[dict]:
    """Topics for testing quiz generation quality."""
    return [
        {
            "topic": "Photosynthesis",
            "expected_keywords": [
                "chlorophyll",
                "sunlight",
                "carbon dioxide",
                "oxygen",
                "glucose",
            ],
        },
        {
            "topic": "American Revolution",
            "expected_keywords": [
                "independence",
                "1776",
                "colonies",
                "Britain",
                "constitution",
            ],
        },
        {
            "topic": "Python Programming",
            "expected_keywords": [
                "syntax",
                "variables",
                "functions",
                "loops",
                "data types",
            ],
        },
    ]


@pytest.fixture
def tool_calling_scenarios() -> list[dict]:
    """Scenarios for testing tool calling accuracy."""
    return [
        {
            "message": "Create a quiz about the solar system",
            "expected_tool": "generate_quiz",
            "expected_params": {"topic": "solar system"},
        },
        {
            "message": "Show me all my quizzes",
            "expected_tool": "list_quizzes",
            "expected_params": {},
        },
        {
            "message": "Delete the quiz called 'Old Quiz'",
            "expected_tool": "delete_quiz",
            "expected_params": {"title": "Old Quiz"},
        },
        {
            "message": "Get the score distribution and analytics for my quiz called 'Python Basics'",
            "expected_tool": "get_quiz_analytics",
            "expected_params": {},  # Requires title extraction
        },
        {
            "message": "Edit my quiz called 'Math' and change its title to 'Advanced Math'",
            "expected_tool": "edit_quiz",
            "expected_params": {"new_title": "Advanced Math"},
        },
    ]
