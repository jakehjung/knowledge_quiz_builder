"""AI benchmark tests for quiz generation quality.

These tests require OPENAI_API_KEY to be set and make real API calls.
Run with: OPENAI_API_KEY=sk-... pytest tests/benchmarks/ -v
"""

import json
import pytest
from typing import Dict, Any, List

from openai import AsyncOpenAI

pytestmark = pytest.mark.benchmark


class TestQuizGenerationQuality:
    """Benchmark tests for AI-generated quiz quality."""

    @pytest.fixture
    def quiz_generation_prompt(self) -> str:
        """Prompt for quiz generation."""
        return """Generate a quiz about {topic}.

Return the quiz as a JSON object with the following structure:
{{
    "title": "Quiz title",
    "description": "Quiz description",
    "questions": [
        {{
            "question_text": "The question",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A|B|C|D",
            "explanation": "Why this answer is correct"
        }}
    ]
}}

Generate exactly 5 questions. Ensure all answers are factually accurate."""

    async def test_quiz_generation_produces_valid_structure(
        self,
        openai_client: AsyncOpenAI,
        quiz_generation_prompt: str,
    ):
        """Test that generated quizzes have valid structure."""
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a quiz generation assistant."},
                {
                    "role": "user",
                    "content": quiz_generation_prompt.format(topic="Basic Mathematics"),
                },
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        quiz_data = json.loads(content)

        # Validate structure
        assert "title" in quiz_data
        assert "questions" in quiz_data
        assert len(quiz_data["questions"]) == 5

        for q in quiz_data["questions"]:
            assert "question_text" in q
            assert "option_a" in q
            assert "option_b" in q
            assert "option_c" in q
            assert "option_d" in q
            assert "correct_answer" in q
            assert q["correct_answer"] in ["A", "B", "C", "D"]

    async def test_quiz_generation_factual_accuracy(
        self,
        openai_client: AsyncOpenAI,
        quiz_generation_topics: List[Dict[str, Any]],
    ):
        """Test that generated quizzes contain expected factual keywords."""
        results = []

        for topic_data in quiz_generation_topics:
            topic = topic_data["topic"]
            expected_keywords = topic_data["expected_keywords"]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a quiz generation assistant. Generate educational quizzes with accurate information. Always respond with valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": f"Generate a 5-question quiz about {topic}. Include explanations for each answer. Return as JSON.",
                    },
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content.lower()

            # Count how many expected keywords appear in the content
            keywords_found = sum(1 for kw in expected_keywords if kw.lower() in content)
            accuracy = keywords_found / len(expected_keywords)

            results.append(
                {
                    "topic": topic,
                    "keywords_found": keywords_found,
                    "total_keywords": len(expected_keywords),
                    "accuracy": accuracy,
                }
            )

        # Calculate overall accuracy
        total_accuracy = sum(r["accuracy"] for r in results) / len(results)

        # Print benchmark results
        print("\n=== Quiz Generation Factual Accuracy ===")
        for r in results:
            print(
                f"  {r['topic']}: {r['keywords_found']}/{r['total_keywords']} ({r['accuracy']*100:.1f}%)"
            )
        print(f"  Overall: {total_accuracy*100:.1f}%")

        # Assert minimum accuracy threshold
        assert (
            total_accuracy >= 0.6
        ), f"Factual accuracy {total_accuracy*100:.1f}% below 60% threshold"

    async def test_quiz_generation_question_clarity(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that generated questions are clear and well-formed."""
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a quiz generation assistant. Always respond with valid JSON."},
                {
                    "role": "user",
                    "content": "Generate a 5-question quiz about world geography. Return as JSON.",
                },
            ],
            response_format={"type": "json_object"},
        )

        quiz_data = json.loads(response.choices[0].message.content)
        questions = quiz_data.get("questions", [])

        clarity_scores = []
        for q in questions:
            question_text = q.get("question_text", "")

            # Basic clarity checks
            score = 0

            # Question ends with question mark
            if question_text.strip().endswith("?"):
                score += 1

            # Question is not too short
            if len(question_text) >= 20:
                score += 1

            # Question is not too long
            if len(question_text) <= 300:
                score += 1

            # Options are distinct (not duplicates)
            options = [
                q.get("option_a", ""),
                q.get("option_b", ""),
                q.get("option_c", ""),
                q.get("option_d", ""),
            ]
            if len(set(options)) == 4:
                score += 1

            # Has explanation
            if q.get("explanation"):
                score += 1

            clarity_scores.append(score / 5)

        avg_clarity = sum(clarity_scores) / len(clarity_scores)

        print("\n=== Question Clarity Score ===")
        print(f"  Average: {avg_clarity*100:.1f}%")

        assert (
            avg_clarity >= 0.8
        ), f"Question clarity {avg_clarity*100:.1f}% below 80% threshold"

    async def test_quiz_generation_explanation_quality(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that generated explanations are helpful and accurate."""
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generation assistant. Always include detailed explanations for why each answer is correct. Respond with valid JSON.",
                },
                {
                    "role": "user",
                    "content": "Generate a 5-question quiz about basic chemistry. Return as JSON.",
                },
            ],
            response_format={"type": "json_object"},
        )

        quiz_data = json.loads(response.choices[0].message.content)
        questions = quiz_data.get("questions", [])

        quality_metrics = {
            "has_explanation": 0,
            "explanation_length_adequate": 0,
            "mentions_correct_answer": 0,
        }

        for q in questions:
            explanation = q.get("explanation", "")
            correct_answer = q.get("correct_answer", "")

            if explanation:
                quality_metrics["has_explanation"] += 1

            if len(explanation) >= 50:
                quality_metrics["explanation_length_adequate"] += 1

            # Check if explanation references the correct option
            correct_option_text = q.get(f"option_{correct_answer.lower()}", "")
            if correct_option_text.lower() in explanation.lower():
                quality_metrics["mentions_correct_answer"] += 1

        total_questions = len(questions)

        print("\n=== Explanation Quality ===")
        for metric, count in quality_metrics.items():
            pct = count / total_questions * 100
            print(f"  {metric}: {count}/{total_questions} ({pct:.1f}%)")

        # All questions should have explanations
        assert quality_metrics["has_explanation"] == total_questions


class TestQuizGenerationWithRAG:
    """Benchmark tests for RAG-enhanced quiz generation."""

    async def test_quiz_with_wikipedia_context(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that providing Wikipedia context improves quiz quality."""
        topic = "Photosynthesis"

        # Simulated Wikipedia context
        wiki_context = """
        Photosynthesis is a biological process used by plants, algae, and certain bacteria
        to convert light energy into chemical energy. The process occurs in chloroplasts
        using chlorophyll, which absorbs light energy (primarily red and blue wavelengths).

        The overall equation for photosynthesis is:
        6CO2 + 6H2O + light energy → C6H12O6 + 6O2

        The process involves two main stages:
        1. Light-dependent reactions (in thylakoid membranes)
        2. Light-independent reactions/Calvin cycle (in stroma)

        Key molecules involved: ATP, NADPH, glucose, oxygen.
        """

        # Generate quiz with context
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generation assistant. Use the provided context to create accurate quiz questions. Respond with valid JSON.",
                },
                {
                    "role": "user",
                    "content": f"""Based on this context about {topic}:

{wiki_context}

Generate a 5-question quiz testing understanding of this topic. Include specific facts from the context. Return as JSON.""",
                },
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.lower()
        quiz_data = json.loads(response.choices[0].message.content)

        # Check that quiz includes specific facts from context
        context_facts = [
            "chlorophyll",
            "chloroplast",
            "co2",
            "oxygen",
            "glucose",
            "calvin cycle",
            "light",
        ]

        facts_found = sum(1 for fact in context_facts if fact in content)
        coverage = facts_found / len(context_facts)

        print("\n=== RAG Context Coverage ===")
        print(
            f"  Facts from context: {facts_found}/{len(context_facts)} ({coverage*100:.1f}%)"
        )

        # RAG should improve fact coverage
        assert (
            coverage >= 0.5
        ), f"Context coverage {coverage*100:.1f}% below 50% threshold"
        assert len(quiz_data.get("questions", [])) == 5
