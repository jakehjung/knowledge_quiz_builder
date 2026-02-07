from pydantic import BaseModel
from typing import Optional, List, Any


class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
    data: Optional[Any] = None
