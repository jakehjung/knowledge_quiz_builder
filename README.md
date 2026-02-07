# AI-Powered Knowledge Quiz Builder

A full-stack quiz app where instructors can create quizzes using an AI chatbot, and students can take them.

**Built for**: System Design Interview

## Quick Start

```bash
# Start PostgreSQL
brew services start postgresql@14
createdb quiz_builder

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit: DATABASE_URL, OPENAI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install && npm run dev
```

Open http://localhost:5173

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["React + TypeScript"]
        Pages["Pages"] --> API["api.ts (Axios)"]
    end

    subgraph Server["FastAPI"]
        Routers["/auth, /quizzes, /attempts, /chat"]
        Services["Services Layer"]
        Routers --> Services
    end

    subgraph External["External"]
        OpenAI["OpenAI GPT-4o"]
        Wiki["Wikipedia API"]
    end

    Client -->|REST| Server
    Services --> External
    Services --> DB[(PostgreSQL)]
```

### AI Quiz Generation Flow

```mermaid
flowchart LR
    A["'Create a quiz about X'"] --> B["Sanitize Input"]
    B --> C["Fetch Wikipedia"]
    C --> D["GPT-4o + Function Calling"]
    D --> E["Save to DB"]
    E --> F["Return Response"]
```

---

## Tech Choices

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | FastAPI | Async, auto OpenAPI docs, great typing |
| Frontend | React + Vite | Fast, TypeScript, modern tooling |
| Database | PostgreSQL | Reliable, good async support |
| ORM | SQLAlchemy 2.0 | Async, type hints, Alembic migrations |
| AI | GPT-4o | Best quality, function calling support |
| RAG | Wikipedia | Free, educational content |
| State | TanStack Query | Server-state caching, auto refresh |
| UI | shadcn/ui + Tailwind | Fast to build, accessible |

### Why Function Calling?

Instead of asking GPT to generate free-form text and parsing it, I use OpenAI's function calling:

```
User: "Create a quiz about space"
  ↓
GPT-4o decides to call: generate_quiz(topic="space", num_questions=5)
  ↓
My code executes that function → saves to DB
  ↓
GPT-4o generates a friendly response
```

This is more reliable than parsing JSON from free-form responses.

### Available AI Tools

- `generate_quiz` - Create quiz with AI-generated questions
- `edit_quiz` - Update title, description, tags
- `delete_quiz` - Remove a quiz
- `list_quizzes` - Search instructor's quizzes
- `get_quiz_analytics` - View stats
- `edit_question` - Modify specific questions
- `add_questions` - Add more questions to existing quiz

---

## Project Structure

```
backend/
├── app/
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   └── ai/             # OpenAI tools & handlers
└── tests/
    ├── unit/           # Service tests (mocked DB)
    ├── integration/    # API tests (real test DB)
    └── benchmarks/     # AI quality tests (real OpenAI)

frontend/
├── src/
│   ├── pages/          # Route components
│   ├── components/     # Reusable UI
│   ├── services/       # API client
│   └── hooks/          # Auth, theme, toast
```

---

## Testing

```bash
cd backend
source venv/bin/activate

# Run tests
pytest tests/unit tests/integration -v

# With coverage
pytest --cov=app --cov-report=html
```

**Coverage**: ~82% across 143 tests

### AI Benchmarks

These make real OpenAI API calls to measure generation quality:

```bash
OPENAI_API_KEY=sk-... pytest tests/benchmarks/ -v
```

Metrics: factual accuracy, question clarity, explanation quality, tool selection accuracy.

---

## API Overview

| Endpoint | What it does |
|----------|--------------|
| `POST /api/auth/register` | Create account (instructor/student) |
| `POST /api/auth/login` | Get JWT tokens |
| `POST /api/auth/refresh` | Refresh access token |
| `GET /api/quizzes` | List/search quizzes |
| `POST /api/quizzes` | Create quiz (instructor) |
| `POST /api/attempts/{quizId}/start` | Start quiz attempt |
| `POST /api/attempts/{id}/submit` | Submit answers |
| `POST /api/chat` | AI chatbot (instructor only) |
| `GET /api/quizzes/{id}/analytics` | Quiz stats (owner only) |

Full docs at http://localhost:8000/docs

---

## Security Notes

**Implemented:**
- Password hashing (bcrypt)
- JWT with refresh tokens (access: 15min, refresh: 7 days hashed in DB)
- Role-based access (instructor vs student)
- Prompt injection filtering for AI input
- CORS configured

**Skipped for MVP:**
- httpOnly cookies (using localStorage)
- Rate limiting
- Email verification

---

## Troubleshooting

**DB connection failed?**
```bash
brew services list  # Check PostgreSQL is running
createdb quiz_builder  # Create the database
```

**OpenAI errors?**
- Check `OPENAI_API_KEY` in `.env`
- Make sure you have GPT-4o access

**Frontend can't connect?**
- Backend running on :8000?
- Check `vite.config.ts` proxy settings

---

## Other Docs

- [PRD.md](./PRD.md) - Product requirements with user flows
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Technical implementation details
