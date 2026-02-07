"""Tool definitions for OpenAI function calling."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Generate a new quiz with AI-created questions on a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The educational topic for the quiz",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional custom title for the quiz",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for categorizing the quiz",
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions (1-5, default 5)",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_quiz",
            "description": "Edit a quiz's properties (title, description, tags)",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz to edit",
                    },
                    "new_title": {"type": "string", "description": "New title"},
                    "description": {"type": "string", "description": "New description"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags",
                    },
                },
                "required": ["quiz_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_quiz",
            "description": "Delete a quiz by title",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz to delete",
                    },
                },
                "required": ["quiz_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_quizzes",
            "description": "List instructor's quizzes with optional search filter",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Optional search term",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quiz_details",
            "description": "Get detailed information about a quiz",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz",
                    },
                },
                "required": ["quiz_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quiz_analytics",
            "description": "Get analytics and statistics for a quiz",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz",
                    },
                },
                "required": ["quiz_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_question",
            "description": "Edit a specific question within a quiz",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz",
                    },
                    "question_number": {
                        "type": "integer",
                        "description": "Question number (1, 2, 3...)",
                        "minimum": 1,
                    },
                    "question_text": {
                        "type": "string",
                        "description": "New question text",
                    },
                    "option_a": {"type": "string", "description": "New option A"},
                    "option_b": {"type": "string", "description": "New option B"},
                    "option_c": {"type": "string", "description": "New option C"},
                    "option_d": {"type": "string", "description": "New option D"},
                    "correct_answer": {
                        "type": "string",
                        "description": "Correct answer (A, B, C, or D)",
                        "enum": ["A", "B", "C", "D"],
                    },
                    "explanation": {"type": "string", "description": "New explanation"},
                },
                "required": ["quiz_title", "question_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_questions",
            "description": "Add new questions to an existing quiz (1-5 at a time)",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_title": {
                        "type": "string",
                        "description": "Title of the quiz",
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic for new questions (defaults to quiz topic)",
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions to add (1-5, default 1)",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["quiz_title"],
            },
        },
    },
]
