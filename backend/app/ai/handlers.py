"""Tool execution handlers for AI chatbot."""

import json
from typing import Any, Dict, List
from uuid import UUID

from openai import AsyncOpenAI

from app.models.quiz import AnswerOption
from app.schemas.quiz import QuestionCreate, QuizCreate, QuizUpdate
from app.services.analytics_service import AnalyticsService
from app.services.quiz_service import QuizService
from app.services.wikipedia_service import WikipediaService


class ToolHandler:
    """Handles execution of AI chatbot tools."""

    def __init__(
        self,
        quiz_service: QuizService,
        analytics_service: AnalyticsService,
        wikipedia_service: WikipediaService,
        openai_client: AsyncOpenAI,
        instructor_id: UUID,
    ):
        self.quiz_service = quiz_service
        self.analytics_service = analytics_service
        self.wikipedia = wikipedia_service
        self.client = openai_client
        self.instructor_id = instructor_id

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool by name and return the result."""
        handlers = {
            "generate_quiz": self._handle_generate_quiz,
            "edit_quiz": self._handle_edit_quiz,
            "delete_quiz": self._handle_delete_quiz,
            "list_quizzes": self._handle_list_quizzes,
            "get_quiz_details": self._handle_get_quiz_details,
            "get_quiz_analytics": self._handle_get_quiz_analytics,
            "edit_question": self._handle_edit_question,
            "add_questions": self._handle_add_questions,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        return await handler(arguments)

    async def _find_quiz_by_title(self, title: str):
        """Find a quiz by title (case-insensitive, partial match)."""
        result = await self.quiz_service.list_quizzes(instructor_id=self.instructor_id)

        # Exact match first
        for quiz in result.quizzes:
            if quiz.title.lower() == title.lower():
                return await self.quiz_service.get_quiz_by_id(quiz.id)

        # Partial match
        title_lower = title.lower()
        for quiz in result.quizzes:
            if title_lower in quiz.title.lower() or quiz.title.lower() in title_lower:
                return await self.quiz_service.get_quiz_by_id(quiz.id)

        return None

    async def _get_available_quiz_titles(self) -> List[str]:
        """Get list of available quiz titles for error messages."""
        result = await self.quiz_service.list_quizzes(instructor_id=self.instructor_id)
        return [q.title for q in result.quizzes]

    async def _generate_questions(
        self, topic: str, num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions using GPT-4o with Wikipedia context."""
        wiki_content = await self.wikipedia.search_and_extract(topic)
        context = (
            f"\n\nReference content from Wikipedia:\n{wiki_content}"
            if wiki_content
            else ""
        )

        prompt = f"""Generate exactly {num_questions} multiple-choice questions about "{topic}".{context}

For each question, provide:
1. The question text
2. Four options (A, B, C, D)
3. The correct answer (A, B, C, or D)
4. An explanation of why the correct answer is right

Return as JSON array:
[{{"question_text": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "..."}}]

Make questions educational, accurate, and appropriate for a general audience."""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational quiz generator. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty response")

        data = json.loads(content)
        questions = data if isinstance(data, list) else data.get("questions", [])
        return questions[:num_questions]

    async def _handle_generate_quiz(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new quiz."""
        topic = args["topic"]
        title = args.get("title", f"Quiz: {topic}")
        tags = args.get("tags", [])
        num_questions = args.get("num_questions", 5)

        questions_data = await self._generate_questions(topic, num_questions)

        questions = [
            QuestionCreate(
                question_text=q["question_text"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_answer=AnswerOption(q["correct_answer"]),
                explanation=q.get("explanation"),
            )
            for q in questions_data
        ]

        quiz = await self.quiz_service.create_quiz(
            QuizCreate(
                title=title,
                description=f"A quiz about {topic}",
                topic=topic,
                tags=tags,
                questions=questions,
            ),
            self.instructor_id,
        )

        return {
            "success": True,
            "title": quiz.title,
            "topic": quiz.topic,
            "question_count": len(questions),
            "message": f"Created quiz '{quiz.title}' with {len(questions)} questions",
        }

    async def _handle_edit_quiz(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Edit quiz properties."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        updated = await self.quiz_service.update_quiz(
            quiz.id,
            QuizUpdate(
                title=args.get("new_title"),
                description=args.get("description"),
                tags=args.get("tags"),
            ),
            self.instructor_id,
        )

        if not updated:
            return {"success": False, "message": "Failed to update quiz"}

        return {"success": True, "message": f"Updated quiz '{updated.title}'"}

    async def _handle_delete_quiz(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a quiz."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        title = quiz.title
        success = await self.quiz_service.delete_quiz(quiz.id, self.instructor_id)

        if not success:
            return {"success": False, "message": "Failed to delete quiz"}

        return {"success": True, "message": f"Deleted quiz '{title}'"}

    async def _handle_list_quizzes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List instructor's quizzes."""
        result = await self.quiz_service.list_quizzes(
            search=args.get("search"),
            instructor_id=self.instructor_id,
        )

        if not result.quizzes:
            return {
                "message": "You haven't created any quizzes yet.",
                "quizzes": [],
                "total": 0,
            }

        return {
            "quizzes": [
                {
                    "title": q.title,
                    "topic": q.topic,
                    "tags": q.tags,
                    "question_count": q.question_count,
                    "created": q.created_at.strftime("%B %d, %Y"),
                }
                for q in result.quizzes
            ],
            "total": result.total,
        }

    async def _handle_get_quiz_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get quiz details."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        sorted_questions = sorted(quiz.questions, key=lambda x: x.order_index)

        return {
            "title": quiz.title,
            "description": quiz.description,
            "topic": quiz.topic,
            "tags": [t.tag for t in quiz.tags],
            "question_count": len(quiz.questions),
            "questions": [
                {
                    "number": idx + 1,
                    "question_text": q.question_text,
                    "options": {
                        "A": q.option_a,
                        "B": q.option_b,
                        "C": q.option_c,
                        "D": q.option_d,
                    },
                    "correct_answer": q.correct_answer.value,
                }
                for idx, q in enumerate(sorted_questions)
            ],
            "created_at": quiz.created_at.strftime("%B %d, %Y"),
        }

    async def _handle_get_quiz_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get quiz analytics."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        analytics = await self.analytics_service.get_quiz_analytics(quiz.id)

        if not analytics:
            return {
                "quiz_title": quiz.title,
                "message": "No students have taken this quiz yet",
                "total_attempts": 0,
                "unique_students": 0,
            }

        total_q = analytics.get("total_questions", 5)
        avg_score = analytics.get("average_score", 0)

        return {
            "quiz_title": analytics.get("quiz_title"),
            "total_attempts": analytics.get("total_attempts", 0),
            "unique_students": analytics.get("unique_students", 0),
            "average_score": f"{avg_score}/{total_q} ({int(avg_score / total_q * 100) if total_q else 0}%)",
            "score_distribution": analytics.get("score_distribution", {}),
            "question_performance": [
                {
                    "question_number": idx + 1,
                    "question_preview": q.get("question_text", "")[:50] + "...",
                    "accuracy": f"{q.get('accuracy_rate', 0):.0f}%",
                }
                for idx, q in enumerate(analytics.get("question_analysis", []))
            ],
            "top_students": [
                {
                    "name": s.get("display_name") or s.get("email", "Unknown"),
                    "best_score": f"{s.get('best_score', 0)}/{total_q}",
                    "attempts": s.get("attempts_count", 0),
                }
                for s in analytics.get("student_scores", [])[:5]
            ],
        }

    async def _handle_edit_question(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a specific question."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        question_num = args["question_number"]
        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)

        if question_num < 1 or question_num > len(sorted_questions):
            return {
                "success": False,
                "message": f"Question {question_num} not found. Quiz has {len(sorted_questions)} questions.",
            }

        updated = await self.quiz_service.update_question(
            quiz_id=quiz.id,
            question_number=question_num,
            instructor_id=self.instructor_id,
            question_text=args.get("question_text"),
            option_a=args.get("option_a"),
            option_b=args.get("option_b"),
            option_c=args.get("option_c"),
            option_d=args.get("option_d"),
            correct_answer=args.get("correct_answer"),
            explanation=args.get("explanation"),
        )

        if not updated:
            return {"success": False, "message": "Failed to update question"}

        changes = []
        for field in [
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "explanation",
        ]:
            if args.get(field):
                changes.append(field.replace("_", " "))
        if args.get("correct_answer"):
            changes.append(f"correct answer (now {args['correct_answer']})")

        return {
            "success": True,
            "message": f"Updated Question {question_num} in '{quiz.title}'",
            "changes": changes,
            "updated_question": {
                "number": question_num,
                "question_text": updated.question_text,
                "options": {
                    "A": updated.option_a,
                    "B": updated.option_b,
                    "C": updated.option_c,
                    "D": updated.option_d,
                },
                "correct_answer": updated.correct_answer.value,
            },
        }

    async def _handle_add_questions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add questions to an existing quiz."""
        quiz = await self._find_quiz_by_title(args["quiz_title"])

        if not quiz:
            return {
                "success": False,
                "message": f"Could not find quiz '{args['quiz_title']}'",
                "available_quizzes": await self._get_available_quiz_titles(),
            }

        topic = args.get("topic") or quiz.topic
        num_questions = args.get("num_questions", 1)

        questions_data = await self._generate_questions(topic, num_questions)

        new_questions = await self.quiz_service.add_questions(
            quiz_id=quiz.id,
            instructor_id=self.instructor_id,
            questions_data=questions_data,
        )

        if not new_questions:
            return {"success": False, "message": "Failed to add questions"}

        return {
            "success": True,
            "message": f"Added {len(new_questions)} question(s) to '{quiz.title}'",
            "questions_added": len(new_questions),
            "total_questions": len(quiz.questions) + len(new_questions),
            "new_questions": [
                {
                    "number": len(quiz.questions) + idx + 1,
                    "question_text": q.question_text[:100] + "..."
                    if len(q.question_text) > 100
                    else q.question_text,
                }
                for idx, q in enumerate(new_questions)
            ],
        }
