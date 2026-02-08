# AI-Powered Knowledge Quiz Builder

A full-stack quiz app where instructors can create quizzes using an AI chatbot, and students can take them.

**Features**:
- AI Assistant helps with CRUD actions on quizzes for instructors.
- Manually create quizes.
- Sign up and Log in: Instructor or Student roles.
- Quiz analytics for both instructors and students.
- BYU & U of U themes 😜.
- Students can take quizzes and see the results.
- Decent UI/UX(not sure if it's responsive though).

**What I didn't do**:
- Quiz options dedupe(there is a unique constraint but AI model doesn't know about existing options when generating).
- Useful loggings or tracings.
- Useful analytics in the UI. There are some, but could use some improvements.
- Tests could be more thorough. But I do have some unit/integration tests and AI benchmark tests that are acceptable.
- Error handling:
  - You might run into some AI hiccups. Since it's not fully agentic, it cannot handle all situations.

**How I used AI to build this app**:
- I used Claude Code to generate code.
- First version of PRD.md was generated with the project requirements.
- Final version of [PRD.md](./PRD.md)(what's in this repo now) was generated with the help of Claude Code's plan mode:
  - Ask Claude Code to interview me with all edge cases and extra feature requirements that I wanted. Asked it to be as thorough as possible.
  - At this point, the PRD was extremely detailed and accurate to what I wanted to build.
  - Generating an accurate PRD was probably 30% of my time spent.
- Claude Code's plan mode then generated the [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for implementing the actual application.
- After reviewing the plan, code generation was executed.
- At this point, the application was about 80% finished.
- The final state of the app came after many iterations for bugs, change of plans etc.

**Built for**: AI Engineer Interview

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **OpenAI API key** with GPT-4o access

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/jakehjung/knowledge_quiz_builder.git
cd knowledge_quiz_builder

# 2. Start PostgreSQL (macOS)
brew services start postgresql@14
createdb quiz_builder

# 3. Backend setup
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Then edit .env and set:
#   DATABASE_URL=postgresql+asyncpg://YOUR_USERNAME@localhost:5432/quiz_builder
#   OPENAI_API_KEY=sk-your-key-here
# (Run `whoami` in terminal to get YOUR_USERNAME)

# 5. Run migrations and start backend
alembic upgrade head
uvicorn app.main:app --reload

# 6. Frontend (open new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Try It Out

1. **Register as Instructor** → access AI chatbot
2. Click chat icon (bottom right) → *"Create a quiz about Python"*
3. Open incognito, **register as Student** → take the quiz

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
# macOS
brew services list  # Check PostgreSQL is running
createdb quiz_builder

# Linux
sudo systemctl status postgresql
sudo -u postgres createdb quiz_builder
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/quiz_builder
```

**OpenAI errors?**
- Check `OPENAI_API_KEY` in `.env`
- Make sure you have GPT-4o access

**Frontend can't connect?**
- Backend running on :8000?
- Check `vite.config.ts` proxy settings

**Tests failing with missing module?**
```bash
pip install aiosqlite  # Required for test database
```

---

## Other Docs

- [PRD.md](./PRD.md) - Product requirements with user flows
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Technical implementation details
