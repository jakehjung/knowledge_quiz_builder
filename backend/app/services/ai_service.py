"""AI service for chatbot interactions."""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.handlers import ToolHandler
from app.ai.prompts import get_system_prompt
from app.ai.tools import TOOLS
from app.config import get_settings
from app.services.analytics_service import AnalyticsService
from app.services.quiz_service import QuizService
from app.services.wikipedia_service import WikipediaService
from app.utils.sanitize import sanitize_for_ai

settings = get_settings()

ASSISTANT_NAMES = {
    "byu": "Cosmo the Cougar",
    "utah": "Swoop the Ute",
}


class AIService:
    """Service for AI-powered quiz chatbot."""

    def __init__(
        self, db: AsyncSession, instructor_id: UUID, theme_preference: str = "byu"
    ):
        self.instructor_id = instructor_id
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.assistant_name = ASSISTANT_NAMES.get(
            theme_preference, ASSISTANT_NAMES["byu"]
        )

        self.tool_handler = ToolHandler(
            quiz_service=QuizService(db),
            analytics_service=AnalyticsService(db),
            wikipedia_service=WikipediaService(),
            openai_client=self.client,
            instructor_id=instructor_id,
        )

    async def chat(
        self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Process a chat message and return the response."""
        messages = self._build_messages(message, conversation_history)

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        actions_taken = []
        all_data = []

        # Process tool calls until final response
        while assistant_message.tool_calls:
            messages.append(assistant_message.model_dump())

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = self._parse_arguments(tool_call.function.arguments)

                result = await self.tool_handler.execute(tool_name, arguments)
                actions_taken.append(tool_name)
                all_data.append(result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            assistant_message = response.choices[0].message

        return {
            "response": assistant_message.content,
            "action_taken": actions_taken[-1] if actions_taken else None,
            "data": all_data[-1] if all_data else None,
        }

    def _build_messages(
        self, message: str, history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Build message list for OpenAI API."""
        messages = [
            {"role": "system", "content": get_system_prompt(self.assistant_name)}
        ]

        if history:
            for msg in history:
                content = (
                    sanitize_for_ai(msg["content"])
                    if msg["role"] == "user"
                    else msg["content"]
                )
                messages.append({"role": msg["role"], "content": content})

        messages.append({"role": "user", "content": sanitize_for_ai(message)})
        return messages

    @staticmethod
    def _parse_arguments(arguments_str: str) -> Dict[str, Any]:
        """Parse tool arguments from JSON string."""
        if not arguments_str:
            return {}
        try:
            return json.loads(arguments_str)
        except json.JSONDecodeError:
            return {}
