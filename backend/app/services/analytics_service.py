from uuid import UUID
from typing import Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz
from app.models.attempt import QuizAttempt, AttemptStatus


class QuestionAnalysis:
    def __init__(
        self,
        question_id: UUID,
        question_text: str,
        correct_count: int,
        incorrect_count: int,
    ):
        self.question_id = question_id
        self.question_text = question_text
        self.correct_count = correct_count
        self.incorrect_count = incorrect_count
        total = correct_count + incorrect_count
        self.accuracy_rate = (correct_count / total * 100) if total > 0 else 0


class StudentScore:
    def __init__(
        self,
        user_id: UUID,
        display_name: str | None,
        email: str,
        best_score: int,
        attempts_count: int,
    ):
        self.user_id = user_id
        self.display_name = display_name
        self.email = email
        self.best_score = best_score
        self.attempts_count = attempts_count


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quiz_analytics(self, quiz_id: UUID) -> dict:
        # Get quiz with questions
        quiz_result = await self.db.execute(
            select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
        )
        quiz = quiz_result.scalar_one_or_none()

        if not quiz:
            return {}

        # Get all completed attempts (excluding the instructor's own attempts)
        attempts_result = await self.db.execute(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.answers), selectinload(QuizAttempt.user))
            .where(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.status == AttemptStatus.COMPLETED,
                    QuizAttempt.user_id != quiz.instructor_id,  # Exclude instructor
                )
            )
        )
        attempts = attempts_result.scalars().all()

        total_attempts = len(attempts)
        unique_users = set(a.user_id for a in attempts)
        unique_students = len(unique_users)

        # Calculate average score
        scores = [a.score for a in attempts if a.score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        total_questions = len(quiz.questions)

        # Score distribution (0 to total_questions)
        score_distribution: Dict[int, int] = {i: 0 for i in range(total_questions + 1)}
        for score in scores:
            if score is not None:
                score_distribution[score] = score_distribution.get(score, 0) + 1

        # Question analysis - sort by order_index for correct Q1, Q2, Q3 labeling
        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)
        question_stats: Dict[str, Dict] = {}
        for question in sorted_questions:
            question_stats[str(question.id)] = {
                "question_text": question.question_text,
                "order_index": question.order_index,
                "correct": 0,
                "incorrect": 0,
            }

        for attempt in attempts:
            for answer in attempt.answers:
                qid = str(answer.question_id)
                if qid in question_stats:
                    if answer.is_correct:
                        question_stats[qid]["correct"] += 1
                    else:
                        question_stats[qid]["incorrect"] += 1

        # Build list sorted by order_index
        question_analysis = sorted(
            [
                {
                    "question_id": qid,
                    "question_text": stats["question_text"],
                    "order_index": stats["order_index"],
                    "correct_count": stats["correct"],
                    "incorrect_count": stats["incorrect"],
                    "accuracy_rate": (
                        stats["correct"] / (stats["correct"] + stats["incorrect"]) * 100
                        if (stats["correct"] + stats["incorrect"]) > 0
                        else 0
                    ),
                }
                for qid, stats in question_stats.items()
            ],
            key=lambda x: x["order_index"],
        )

        # Student scores (best score per student)
        student_scores_map: Dict[str, Dict] = {}
        for attempt in attempts:
            uid = str(attempt.user_id)
            if uid not in student_scores_map:
                student_scores_map[uid] = {
                    "user_id": attempt.user_id,
                    "display_name": attempt.user.display_name,
                    "email": attempt.user.email,
                    "best_score": attempt.score or 0,
                    "attempts_count": 1,
                }
            else:
                student_scores_map[uid]["attempts_count"] += 1
                if (attempt.score or 0) > student_scores_map[uid]["best_score"]:
                    student_scores_map[uid]["best_score"] = attempt.score or 0

        # Sort by best score descending for leaderboard
        student_scores = sorted(
            student_scores_map.values(), key=lambda x: x["best_score"], reverse=True
        )

        return {
            "quiz_id": str(quiz_id),
            "quiz_title": quiz.title,
            "total_questions": total_questions,
            "total_attempts": total_attempts,
            "unique_students": unique_students,
            "average_score": round(average_score, 2),
            "score_distribution": score_distribution,
            "question_analysis": question_analysis,
            "student_scores": student_scores,
        }

    async def get_instructor_dashboard_stats(self, instructor_id: UUID) -> dict:
        """Get aggregated stats for an instructor's dashboard."""
        # Get all quizzes by this instructor with questions loaded
        quizzes_result = await self.db.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.instructor_id == instructor_id)
        )
        quizzes = quizzes_result.scalars().all()
        quiz_ids = [q.id for q in quizzes]

        if not quiz_ids:
            return {
                "total_quizzes": 0,
                "total_students": 0,
                "total_attempts": 0,
                "average_percentage": 0,
            }

        # Create a map of quiz_id to question count
        quiz_question_counts = {q.id: len(q.questions) for q in quizzes}

        # Get all completed attempts for these quizzes (excluding instructor's own)
        attempts_result = await self.db.execute(
            select(QuizAttempt).where(
                and_(
                    QuizAttempt.quiz_id.in_(quiz_ids),
                    QuizAttempt.status == AttemptStatus.COMPLETED,
                    QuizAttempt.user_id != instructor_id,
                )
            )
        )
        attempts = attempts_result.scalars().all()

        total_attempts = len(attempts)
        unique_students = len(set(a.user_id for a in attempts))

        # Calculate average percentage (score / total_questions * 100 for each attempt)
        percentages = []
        for a in attempts:
            if a.score is not None:
                total_q = quiz_question_counts.get(a.quiz_id, 5)
                if total_q > 0:
                    percentages.append((a.score / total_q) * 100)

        average_percentage = sum(percentages) / len(percentages) if percentages else 0

        return {
            "total_quizzes": len(quizzes),
            "total_students": unique_students,
            "total_attempts": total_attempts,
            "average_percentage": round(average_percentage, 1),
        }
