from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz, Question, QuizTag, AnswerOption
from app.models.attempt import QuizAttempt
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizListItem,
    QuizListResponse,
    SortOrder,
)


class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_quiz(self, quiz_data: QuizCreate, instructor_id: UUID) -> Quiz:
        # Create quiz
        quiz = Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            topic=quiz_data.topic,
            instructor_id=instructor_id,
        )
        self.db.add(quiz)
        await self.db.flush()

        # Add tags
        if quiz_data.tags:
            for tag in quiz_data.tags:
                quiz_tag = QuizTag(quiz_id=quiz.id, tag=tag)
                self.db.add(quiz_tag)

        # Add questions
        for idx, q_data in enumerate(quiz_data.questions):
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                option_a=q_data.option_a,
                option_b=q_data.option_b,
                option_c=q_data.option_c,
                option_d=q_data.option_d,
                correct_answer=q_data.correct_answer,
                explanation=q_data.explanation,
                order_index=idx,
            )
            self.db.add(question)

        await self.db.commit()
        await self.db.refresh(quiz)

        # Reload with relationships
        return await self.get_quiz_by_id(quiz.id)

    async def get_quiz_by_id(self, quiz_id: UUID) -> Optional[Quiz]:
        result = await self.db.execute(
            select(Quiz)
            .options(
                selectinload(Quiz.questions),
                selectinload(Quiz.tags),
                selectinload(Quiz.instructor),
            )
            .where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()

    async def list_quizzes(
        self,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort: SortOrder = SortOrder.NEWEST,
        page: int = 1,
        page_size: int = 10,
        instructor_id: Optional[UUID] = None,
    ) -> QuizListResponse:
        query = (
            select(Quiz)
            .options(
                selectinload(Quiz.tags),
                selectinload(Quiz.instructor),
                selectinload(Quiz.questions),
            )
            .where(Quiz.is_published.is_(True))
        )

        if instructor_id:
            query = query.where(Quiz.instructor_id == instructor_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Quiz.title.ilike(search_pattern),
                    Quiz.description.ilike(search_pattern),
                    Quiz.topic.ilike(search_pattern),
                )
            )

        if tags:
            # Filter quizzes that have any of the specified tags
            query = query.where(
                Quiz.id.in_(select(QuizTag.quiz_id).where(QuizTag.tag.in_(tags)))
            )

        # Sorting
        if sort == SortOrder.NEWEST:
            query = query.order_by(Quiz.created_at.desc())
        elif sort == SortOrder.OLDEST:
            query = query.order_by(Quiz.created_at.asc())
        elif sort == SortOrder.ALPHABETICAL:
            query = query.order_by(Quiz.title.asc())
        elif sort == SortOrder.POPULAR:
            # Sort by attempt count
            subquery = (
                select(
                    QuizAttempt.quiz_id,
                    func.count(QuizAttempt.id).label("attempt_count"),
                )
                .group_by(QuizAttempt.quiz_id)
                .subquery()
            )
            query = query.outerjoin(subquery, Quiz.id == subquery.c.quiz_id).order_by(
                func.coalesce(subquery.c.attempt_count, 0).desc()
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        quizzes = result.scalars().all()

        quiz_items = [
            QuizListItem(
                id=q.id,
                title=q.title,
                description=q.description,
                topic=q.topic,
                tags=[t.tag for t in q.tags],
                instructor=q.instructor,
                is_published=q.is_published,
                created_at=q.created_at,
                question_count=len(q.questions),
            )
            for q in quizzes
        ]

        return QuizListResponse(
            quizzes=quiz_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_instructor_quizzes(self, instructor_id: UUID) -> QuizListResponse:
        query = (
            select(Quiz)
            .options(
                selectinload(Quiz.tags),
                selectinload(Quiz.instructor),
                selectinload(Quiz.questions),
            )
            .where(Quiz.instructor_id == instructor_id)
            .order_by(Quiz.created_at.desc())
        )

        result = await self.db.execute(query)
        quizzes = result.scalars().all()

        quiz_items = [
            QuizListItem(
                id=q.id,
                title=q.title,
                description=q.description,
                topic=q.topic,
                tags=[t.tag for t in q.tags],
                instructor=q.instructor,
                is_published=q.is_published,
                created_at=q.created_at,
                question_count=len(q.questions),
            )
            for q in quizzes
        ]

        return QuizListResponse(
            quizzes=quiz_items,
            total=len(quiz_items),
            page=1,
            page_size=len(quiz_items),
        )

    async def update_quiz(
        self, quiz_id: UUID, update_data: QuizUpdate, instructor_id: UUID
    ) -> Optional[Quiz]:
        quiz = await self.get_quiz_by_id(quiz_id)

        if not quiz or quiz.instructor_id != instructor_id:
            return None

        if update_data.title is not None:
            quiz.title = update_data.title
        if update_data.description is not None:
            quiz.description = update_data.description
        if update_data.topic is not None:
            quiz.topic = update_data.topic
        if update_data.is_published is not None:
            quiz.is_published = update_data.is_published

        if update_data.tags is not None:
            # Delete existing tags
            await self.db.execute(delete(QuizTag).where(QuizTag.quiz_id == quiz_id))
            # Add new tags
            for tag in update_data.tags:
                quiz_tag = QuizTag(quiz_id=quiz_id, tag=tag)
                self.db.add(quiz_tag)

        if update_data.questions is not None:
            # Delete existing questions
            await self.db.execute(delete(Question).where(Question.quiz_id == quiz_id))
            # Add new questions
            for idx, q_data in enumerate(update_data.questions):
                question = Question(
                    quiz_id=quiz_id,
                    question_text=q_data.question_text,
                    option_a=q_data.option_a,
                    option_b=q_data.option_b,
                    option_c=q_data.option_c,
                    option_d=q_data.option_d,
                    correct_answer=q_data.correct_answer,
                    explanation=q_data.explanation,
                    order_index=idx,
                )
                self.db.add(question)

        await self.db.commit()
        return await self.get_quiz_by_id(quiz_id)

    async def delete_quiz(self, quiz_id: UUID, instructor_id: UUID) -> bool:
        quiz = await self.get_quiz_by_id(quiz_id)

        if not quiz or quiz.instructor_id != instructor_id:
            return False

        await self.db.delete(quiz)
        await self.db.commit()
        return True

    async def update_question(
        self,
        quiz_id: UUID,
        question_number: int,
        instructor_id: UUID,
        question_text: Optional[str] = None,
        option_a: Optional[str] = None,
        option_b: Optional[str] = None,
        option_c: Optional[str] = None,
        option_d: Optional[str] = None,
        correct_answer: Optional[str] = None,
        explanation: Optional[str] = None,
    ) -> Optional[Question]:
        """Update a specific question within a quiz by question number (1-5)."""
        quiz = await self.get_quiz_by_id(quiz_id)

        if not quiz or quiz.instructor_id != instructor_id:
            return None

        # Sort questions by order_index and get the one at question_number - 1
        sorted_questions = sorted(quiz.questions, key=lambda q: q.order_index)
        if question_number < 1 or question_number > len(sorted_questions):
            return None

        question = sorted_questions[question_number - 1]

        # Update fields if provided
        if question_text is not None:
            question.question_text = question_text
        if option_a is not None:
            question.option_a = option_a
        if option_b is not None:
            question.option_b = option_b
        if option_c is not None:
            question.option_c = option_c
        if option_d is not None:
            question.option_d = option_d
        if correct_answer is not None:
            question.correct_answer = AnswerOption(correct_answer.upper())
        if explanation is not None:
            question.explanation = explanation

        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def add_questions(
        self,
        quiz_id: UUID,
        instructor_id: UUID,
        questions_data: List[dict],
    ) -> Optional[List[Question]]:
        """Add new questions to an existing quiz."""
        quiz = await self.get_quiz_by_id(quiz_id)

        if not quiz or quiz.instructor_id != instructor_id:
            return None

        # Get the current highest order_index
        current_max_index = max((q.order_index for q in quiz.questions), default=-1)

        new_questions = []
        for idx, q_data in enumerate(questions_data):
            question = Question(
                quiz_id=quiz_id,
                question_text=q_data["question_text"],
                option_a=q_data["option_a"],
                option_b=q_data["option_b"],
                option_c=q_data["option_c"],
                option_d=q_data["option_d"],
                correct_answer=AnswerOption(q_data["correct_answer"]),
                explanation=q_data.get("explanation"),
                order_index=current_max_index + 1 + idx,
            )
            self.db.add(question)
            new_questions.append(question)

        await self.db.commit()

        # Refresh all new questions
        for q in new_questions:
            await self.db.refresh(q)

        return new_questions
