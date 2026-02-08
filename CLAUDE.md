# CLAUDE.md

This file provides context for Claude (or any AI assistant) working on this codebase.

## Project Overview

AI-powered quiz builder with:
- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **Frontend**: React + TypeScript + Vite + TanStack Query
- **AI**: OpenAI GPT-4o with Function Calling + Wikipedia RAG

## Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload          # Run server
pytest tests/unit tests/integration -v  # Run tests
pytest --cov=app --cov-report=html      # Coverage report
alembic upgrade head                    # Run migrations
alembic revision --autogenerate -m "msg" # Create migration

# Frontend
cd frontend
npm run dev      # Dev server
npm run build    # Production build
npm run lint     # ESLint
```

## Architecture

```
backend/
├── app/
│   ├── main.py           # FastAPI app, CORS, router registration
│   ├── config.py         # Pydantic settings (from .env)
│   ├── database.py       # Async SQLAlchemy engine
│   ├── dependencies.py   # Auth dependencies (get_current_user)
│   ├── routers/          # API endpoints (thin, delegate to services)
│   ├── services/         # Business logic (all DB operations here)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── ai/               # OpenAI tools, handlers, prompts
│   └── utils/            # Helpers (auth, sanitize)
└── tests/
    ├── conftest.py       # Shared fixtures, test DB setup
    ├── unit/             # Service tests with mocked DB
    ├── integration/      # API tests with real test DB
    └── benchmarks/       # AI quality tests (real OpenAI calls)

frontend/
├── src/
│   ├── pages/            # Route components
│   ├── components/       # Reusable UI (shadcn/ui)
│   ├── services/api.ts   # Axios with token refresh
│   ├── store/            # Auth & Theme contexts
│   ├── hooks/            # Custom hooks
│   ├── lib/utils.ts      # cn() helper for Tailwind
│   └── types/            # TypeScript interfaces
```

## Code Patterns

### Backend

**Routers are thin** - just validation and delegation:
```python
@router.post("/quizzes")
async def create_quiz(
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_instructor),
):
    service = QuizService(db)
    return await service.create_quiz(data, user.id)
```

**Services contain business logic**:
```python
class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_quiz(self, data: QuizCreate, user_id: UUID) -> Quiz:
        quiz = Quiz(title=data.title, instructor_id=user_id, ...)
        self.db.add(quiz)
        await self.db.commit()
        return quiz
```

**Use SQLAlchemy 2.0 style**:
```python
# Good
result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
quiz = result.scalar_one_or_none()

# Bad (1.x style)
quiz = db.query(Quiz).filter_by(id=quiz_id).first()
```

**Async everywhere** - all DB operations and external calls use `async/await`.

### Frontend

**Use TanStack Query for server state**:
```typescript
const { data: quizzes, isLoading } = useQuery({
  queryKey: ['quizzes'],
  queryFn: () => api.get('/api/quizzes').then(r => r.data),
});
```

**API client with auto token refresh** - see `services/api.ts`.

**shadcn/ui components** - copy-paste from ui.shadcn.com, customize in `components/ui/`.

### AI Integration

**Function Calling pattern** - AI chooses tools, we execute:
```python
# 1. Define tools in ai/tools.py
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Create a new quiz",
            "parameters": {...}
        }
    }
]

# 2. Handle tool calls in ai/handlers.py
async def handle_tool_call(tool_name: str, args: dict, ...):
    if tool_name == "generate_quiz":
        return await generate_quiz_handler(args, ...)

# 3. Loop until no more tool calls
while response.tool_calls:
    # Execute tools, feed results back to GPT
```

**Wikipedia RAG** - fetch context before quiz generation:
```python
wiki_content = await wikipedia_service.get_extract(topic)
messages.append({"role": "user", "content": f"Context:\n{wiki_content}\n\n{user_message}"})
```

## Database

**PostgreSQL** in production, **SQLite** in tests (with UUID workaround in conftest.py).

**Models use UUID primary keys**:
```python
class Quiz(Base):
    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
```

**Migrations with Alembic** - never modify models without creating a migration.

## Testing

**Unit tests** - mock the database session:
```python
async def test_create_quiz(db_session):
    service = QuizService(db_session)
    quiz = await service.create_quiz(data, user_id)
    assert quiz.title == "Test"
```

**Integration tests** - use TestClient with real test DB:
```python
async def test_create_quiz_endpoint(client, instructor_token):
    response = await client.post(
        "/api/quizzes",
        json={"title": "Test"},
        headers={"Authorization": f"Bearer {instructor_token}"}
    )
    assert response.status_code == 201
```

**AI benchmarks** - real OpenAI calls, measure quality metrics.

## Auth

- JWT access tokens (15min) + refresh tokens (7 days, hashed in DB)
- Two roles: `instructor` (can create quizzes, use AI) and `student` (can take quizzes)
- `get_current_user` dependency extracts user from token
- `require_instructor` dependency checks role

## Common Gotchas

1. **SQLite UUID** - Tests use SQLite which doesn't have native UUID. See conftest.py workaround.

2. **Async sessions** - Always use `async with` or let FastAPI's Depends handle cleanup.

3. **Token refresh** - Frontend Axios interceptor auto-refreshes on 401.

4. **CORS** - Configured in main.py for frontend origin.

5. **OpenAI JSON mode** - Must include "json" in the prompt when using `response_format={"type": "json_object"}`.

## Style Guide

- Python: Black formatter, Ruff linter
- TypeScript: ESLint + Prettier
- Commits: Conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- No comments explaining obvious code
- Type hints everywhere (Python 3.11+ syntax: `str | None` not `Optional[str]`)
