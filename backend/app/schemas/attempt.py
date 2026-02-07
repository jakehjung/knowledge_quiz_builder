from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from app.models.quiz import AnswerOption
from app.models.attempt import AttemptStatus


class AttemptStart(BaseModel):
    quiz_id: UUID


class AttemptAnswerSave(BaseModel):
    question_id: UUID
    selected_answer: Optional[AnswerOption] = None


class AttemptSubmit(BaseModel):
    answers: List[AttemptAnswerSave]


class AttemptAnswerResponse(BaseModel):
    question_id: UUID
    selected_answer: Optional[AnswerOption]
    is_correct: Optional[bool]

    class Config:
        from_attributes = True


class AttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    status: AttemptStatus
    score: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    answers: List[AttemptAnswerResponse]

    class Config:
        from_attributes = True


class QuestionResultResponse(BaseModel):
    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: AnswerOption
    explanation: Optional[str]
    selected_answer: Optional[AnswerOption]
    is_correct: Optional[bool]


class AttemptResultResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    quiz_title: str
    status: AttemptStatus
    score: Optional[int]
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime]
    questions: List[QuestionResultResponse]


class AttemptSummary(BaseModel):
    id: UUID
    quiz_id: UUID
    quiz_title: str
    status: AttemptStatus
    score: Optional[int]
    total_questions: int = 5
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserAttemptsResponse(BaseModel):
    attempts: List[AttemptSummary]
    total: int
