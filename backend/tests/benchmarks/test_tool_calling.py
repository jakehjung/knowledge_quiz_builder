"""AI benchmark tests for tool calling accuracy.

These tests require OPENAI_API_KEY to be set and make real API calls.
Run with: OPENAI_API_KEY=sk-... pytest tests/benchmarks/ -v
"""

import json
import pytest
from typing import Dict, Any, List

from openai import AsyncOpenAI

from app.ai.tools import TOOLS
from app.ai.prompts import get_system_prompt

pytestmark = pytest.mark.benchmark


class TestToolSelectionAccuracy:
    """Benchmark tests for correct tool selection."""

    async def test_tool_selection_for_quiz_generation(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that quiz generation requests trigger generate_quiz tool."""
        messages = [
            {"role": "system", "content": get_system_prompt("Quiz Assistant")},
            {"role": "user", "content": "Create a quiz about the French Revolution"},
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        assert message.tool_calls is not None, "Expected tool call but got none"
        assert len(message.tool_calls) > 0

        tool_names = [tc.function.name for tc in message.tool_calls]
        assert (
            "generate_quiz" in tool_names
        ), f"Expected generate_quiz, got {tool_names}"

    async def test_tool_selection_for_list_quizzes(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that list requests trigger list_quizzes tool."""
        messages = [
            {"role": "system", "content": get_system_prompt("Quiz Assistant")},
            {"role": "user", "content": "Show me all my quizzes"},
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        assert message.tool_calls is not None
        tool_names = [tc.function.name for tc in message.tool_calls]
        assert "list_quizzes" in tool_names, f"Expected list_quizzes, got {tool_names}"

    async def test_tool_selection_for_delete(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that delete requests trigger delete_quiz tool."""
        messages = [
            {"role": "system", "content": get_system_prompt("Quiz Assistant")},
            {"role": "user", "content": "Delete my quiz called 'Old Math Quiz'"},
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        assert message.tool_calls is not None
        tool_names = [tc.function.name for tc in message.tool_calls]
        assert "delete_quiz" in tool_names, f"Expected delete_quiz, got {tool_names}"

    async def test_tool_selection_for_analytics(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that analytics requests trigger get_quiz_analytics tool."""
        messages = [
            {"role": "system", "content": get_system_prompt("Quiz Assistant")},
            {"role": "user", "content": "Get the score distribution and student performance analytics for my quiz titled 'Python Basics'"},
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        assert message.tool_calls is not None
        tool_names = [tc.function.name for tc in message.tool_calls]
        # Accept get_quiz_analytics OR list_quizzes (model may want to find quiz first)
        valid_tools = ["get_quiz_analytics", "list_quizzes"]
        assert any(
            t in tool_names for t in valid_tools
        ), f"Expected get_quiz_analytics or list_quizzes, got {tool_names}"

    async def test_tool_selection_for_edit(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that edit requests trigger edit_quiz tool."""
        messages = [
            {"role": "system", "content": get_system_prompt("Quiz Assistant")},
            {
                "role": "user",
                "content": "Edit my quiz called 'History' and change its title to 'World History 101'",
            },
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        assert message.tool_calls is not None
        tool_names = [tc.function.name for tc in message.tool_calls]
        assert "edit_quiz" in tool_names, f"Expected edit_quiz, got {tool_names}"


class TestToolParameterExtraction:
    """Benchmark tests for correct parameter extraction."""

    async def test_topic_extraction_for_quiz_generation(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that topic is correctly extracted for quiz generation."""
        test_cases = [
            ("Create a quiz about quantum physics", "quantum physics"),
            ("Make me a quiz on world history", "world history"),
            ("Generate 5 questions about machine learning", "machine learning"),
        ]

        results = []
        for message, expected_topic in test_cases:
            messages = [
                {"role": "system", "content": get_system_prompt("Quiz Assistant")},
                {"role": "user", "content": message},
            ]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc.function.name == "generate_quiz":
                        args = json.loads(tc.function.arguments)
                        extracted_topic = args.get("topic", "").lower()
                        matches = expected_topic.lower() in extracted_topic
                        results.append(
                            {
                                "input": message,
                                "expected": expected_topic,
                                "extracted": extracted_topic,
                                "matches": matches,
                            }
                        )

        accuracy = (
            sum(1 for r in results if r["matches"]) / len(results) if results else 0
        )

        print("\n=== Topic Extraction Accuracy ===")
        for r in results:
            status = "OK" if r["matches"] else "FAIL"
            print(f"  [{status}] '{r['expected']}' -> '{r['extracted']}'")
        print(f"  Overall: {accuracy*100:.1f}%")

        assert (
            accuracy >= 0.8
        ), f"Topic extraction accuracy {accuracy*100:.1f}% below 80%"

    async def test_title_extraction_for_operations(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that quiz titles are correctly extracted for operations."""
        test_cases = [
            ("Delete my 'Python Basics' quiz", "delete_quiz", "python basics"),
            ("Show analytics for 'Math Test'", "get_quiz_analytics", "math test"),
            ("Update the title of 'Old Quiz' to 'New Quiz'", "edit_quiz", "old quiz"),
        ]

        results = []
        for message, expected_tool, expected_title in test_cases:
            messages = [
                {"role": "system", "content": get_system_prompt("Quiz Assistant")},
                {"role": "user", "content": message},
            ]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc.function.name == expected_tool:
                        args = json.loads(tc.function.arguments)
                        # Title might be in 'title' or 'quiz_title' parameter
                        extracted_title = (
                            args.get("title", "") or args.get("quiz_title", "")
                        ).lower()
                        matches = expected_title in extracted_title
                        results.append(
                            {
                                "input": message,
                                "tool": expected_tool,
                                "expected": expected_title,
                                "extracted": extracted_title,
                                "matches": matches,
                            }
                        )

        accuracy = (
            sum(1 for r in results if r["matches"]) / len(results) if results else 0
        )

        print("\n=== Title Extraction Accuracy ===")
        for r in results:
            status = "OK" if r["matches"] else "FAIL"
            print(f"  [{status}] {r['tool']}: '{r['expected']}' -> '{r['extracted']}'")
        print(f"  Overall: {accuracy*100:.1f}%")

        # Title extraction can be tricky, lower threshold
        assert (
            accuracy >= 0.6
        ), f"Title extraction accuracy {accuracy*100:.1f}% below 60%"


class TestToolCallingOverall:
    """Overall tool calling benchmark."""

    async def test_overall_tool_selection_accuracy(
        self,
        openai_client: AsyncOpenAI,
        tool_calling_scenarios: List[Dict[str, Any]],
    ):
        """Test overall accuracy of tool selection across scenarios."""
        results = []

        for scenario in tool_calling_scenarios:
            messages = [
                {"role": "system", "content": get_system_prompt("Quiz Assistant")},
                {"role": "user", "content": scenario["message"]},
            ]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            actual_tool = None

            if msg.tool_calls:
                actual_tool = msg.tool_calls[0].function.name

            correct = actual_tool == scenario["expected_tool"]
            results.append(
                {
                    "message": scenario["message"][:50] + "...",
                    "expected": scenario["expected_tool"],
                    "actual": actual_tool,
                    "correct": correct,
                }
            )

        accuracy = sum(1 for r in results if r["correct"]) / len(results)

        print("\n=== Overall Tool Selection Accuracy ===")
        for r in results:
            status = "OK" if r["correct"] else "FAIL"
            print(f"  [{status}] {r['message']}")
            print(f"         Expected: {r['expected']}, Got: {r['actual']}")
        print(f"\n  Accuracy: {accuracy*100:.1f}%")

        # Tool selection threshold - 60% for MVP (model may list quizzes first to find them)
        assert accuracy >= 0.6, f"Tool selection accuracy {accuracy*100:.1f}% below 60%"


class TestNonToolMessages:
    """Test that non-actionable messages don't trigger tools."""

    async def test_greeting_no_tool_call(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that greetings don't trigger tool calls."""
        greetings = [
            "Hello!",
            "Hi there!",
            "Good morning!",
            "Hey, how are you?",
        ]

        no_tool_count = 0
        for greeting in greetings:
            messages = [
                {"role": "system", "content": get_system_prompt("Quiz Assistant")},
                {"role": "user", "content": greeting},
            ]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            if not msg.tool_calls:
                no_tool_count += 1

        accuracy = no_tool_count / len(greetings)
        print("\n=== Greeting Handling ===")
        print(
            f"  No-tool responses: {no_tool_count}/{len(greetings)} ({accuracy*100:.1f}%)"
        )

        # Most greetings should not trigger tools
        assert accuracy >= 0.75, f"Greeting handling {accuracy*100:.1f}% below 75%"

    async def test_general_question_no_tool_call(
        self,
        openai_client: AsyncOpenAI,
    ):
        """Test that general questions don't trigger inappropriate tool calls."""
        questions = [
            "What can you help me with?",
            "How do I use this system?",
            "What kinds of quizzes can you create?",
        ]

        appropriate_count = 0
        for question in questions:
            messages = [
                {"role": "system", "content": get_system_prompt("Quiz Assistant")},
                {"role": "user", "content": question},
            ]

            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            # Either no tool call or appropriate informational response
            if not msg.tool_calls or (msg.content and len(msg.content) > 50):
                appropriate_count += 1

        accuracy = appropriate_count / len(questions)
        print("\n=== General Question Handling ===")
        print(f"  Appropriate responses: {appropriate_count}/{len(questions)}")

        assert accuracy >= 0.6
