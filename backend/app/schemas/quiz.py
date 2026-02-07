from pydantic import BaseModel, Field, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.models.quiz import AnswerOption


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_answer: AnswerOption
    explanation: Optional[str] = None

    @model_validator(mode="after")
    def validate_no_duplicate_options(self):
        options = [
            self.option_a.strip().lower(),
            self.option_b.strip().lower(),
            self.option_c.strip().lower(),
            self.option_d.strip().lower(),
        ]
        if len(options) != len(set(options)):
            raise ValueError(
                "All answer options must be unique (no duplicates allowed)"
            )
        return self


class QuestionResponse(BaseModel):
    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: AnswerOption
    explanation: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


class QuestionResponseForStudent(BaseModel):
    """Question response without correct_answer and explanation - safe for students"""

    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    order_index: int

    class Config:
        from_attributes = True


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[AnswerOption] = None
    explanation: Optional[str] = None


class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    topic: str = Field(..., min_length=1, max_length=255)
    tags: Optional[List[str]] = None
    questions: List[QuestionCreate] = Field(..., min_length=1)


class QuizInstructorInfo(BaseModel):
    id: UUID
    display_name: Optional[str]
    email: str

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    topic: str
    tags: List[str]
    questions: List[QuestionResponse]
    instructor: QuizInstructorInfo
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_tags(cls, quiz):
        return cls(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            topic=quiz.topic,
            tags=[t.tag for t in quiz.tags],
            questions=quiz.questions,
            instructor=quiz.instructor,
            is_published=quiz.is_published,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )


class QuizResponseForStudent(BaseModel):
    """Quiz response without correct answers - safe for students taking the quiz"""

    id: UUID
    title: str
    description: Optional[str]
    topic: str
    tags: List[str]
    questions: List[QuestionResponseForStudent]
    instructor: QuizInstructorInfo
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_tags(cls, quiz):
        return cls(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            topic=quiz.topic,
            tags=[t.tag for t in quiz.tags],
            questions=[
                QuestionResponseForStudent.model_validate(q) for q in quiz.questions
            ],
            instructor=quiz.instructor,
            is_published=quiz.is_published,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )


class QuizListItem(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    topic: str
    tags: List[str]
    instructor: QuizInstructorInfo
    is_published: bool
    created_at: datetime
    question_count: int = 5

    class Config:
        from_attributes = True


class QuizListResponse(BaseModel):
    quizzes: List[QuizListItem]
    total: int
    page: int
    page_size: int


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    topic: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    questions: Optional[List[QuestionCreate]] = None


class SortOrder(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    ALPHABETICAL = "alphabetical"
    POPULAR = "popular"


class QuizSearchParams(BaseModel):
    search: Optional[str] = None
    tags: Optional[List[str]] = None
    sort: SortOrder = SortOrder.NEWEST
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
