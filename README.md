# AI-Powered Knowledge Quiz Builder

A full-stack web application that enables instructors to create AI-generated multiple-choice quizzes and allows students to discover, take, and review quizzes with instant feedback.

**Built for**: AI Engineer System Design Interview

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Technical Decisions](#technical-decisions)
4. [AI Integration & Reasoning](#ai-integration--reasoning)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Setup Instructions](#setup-instructions)
8. [Running the Application](#running-the-application)
9. [Testing](#testing)
10. [API Reference](#api-reference)
11. [Features Overview](#features-overview)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Start PostgreSQL (macOS)
brew services start postgresql@14
createdb quiz_builder

# 2. Backend (Terminal 1)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: Set DATABASE_URL and OPENAI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# Open http://localhost:5173
```

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  CLIENT                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     React + TypeScript (Vite)                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Pages     │  │ Components  │  │   Hooks     │  │  Services   │  │  │
│  │  │  - Login    │  │  - ChatPanel│  │  - useAuth  │  │  - api.ts   │  │  │
│  │  │  - Quiz*    │  │  - Layout   │  │  - useTheme │  │  (Axios +   │  │  │
│  │  │  - Analytics│  │  - Mascots  │  │  - useToast │  │   refresh)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────┬──────┘  │  │
│  └────────────────────────────────────────────────────────────┼──────────┘  │
└───────────────────────────────────────────────────────────────┼─────────────┘
                                                                │
                                                    REST API (JSON)
                                                                │
┌───────────────────────────────────────────────────────────────┼─────────────┐
│                                  SERVER                       │              │
│  ┌────────────────────────────────────────────────────────────┼──────────┐  │
│  │                      FastAPI (Python 3.11+)                │          │  │
│  │  ┌─────────────────────────────────────────────────────────┼───────┐  │  │
│  │  │                       ROUTERS                           │       │  │  │
│  │  │  /api/auth/*  /api/quizzes/*  /api/attempts/*  /api/chat│       │  │  │
│  │  └─────────────────────────────────────────────────────────┼───────┘  │  │
│  │                              │                             │          │  │
│  │  ┌───────────────────────────▼─────────────────────────────▼───────┐  │  │
│  │  │                        SERVICES                                 │  │  │
│  │  │  AuthService  QuizService  AttemptService  AIService  Analytics │  │  │
│  │  └───────────────────────────┬─────────────────────┬───────────────┘  │  │
│  │                              │                     │                  │  │
│  │  ┌───────────────────────────▼──────┐   ┌─────────▼───────────────┐  │  │
│  │  │      SQLAlchemy 2.0 (Async)      │   │    External Services    │  │  │
│  │  │  User, Quiz, Question, Attempt   │   │  ┌─────────────────┐    │  │  │
│  │  └───────────────┬──────────────────┘   │  │  OpenAI GPT-4o  │    │  │  │
│  │                  │                       │  │  (Function      │    │  │  │
│  │                  │                       │  │   Calling)      │    │  │  │
│  │                  │                       │  └─────────────────┘    │  │  │
│  │                  │                       │  ┌─────────────────┐    │  │  │
│  │                  │                       │  │  Wikipedia API  │    │  │  │
│  │                  │                       │  │  (RAG Context)  │    │  │  │
│  └──────────────────┼───────────────────────┴──┴─────────────────┴────┘  │
│                     │                                                     │
└─────────────────────┼─────────────────────────────────────────────────────┘
                      │
           ┌──────────▼──────────┐
           │    PostgreSQL 15    │
           │  ┌───────────────┐  │
           │  │ users         │  │
           │  │ quizzes       │  │
           │  │ questions     │  │
           │  │ quiz_attempts │  │
           │  │ attempt_answer│  │
           │  │ refresh_tokens│  │
           │  └───────────────┘  │
           └─────────────────────┘
```

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        QUIZ GENERATION FLOW                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Instructor sends: "Create a quiz about photosynthesis"               │
│                              │                                           │
│                              ▼                                           │
│  2. Input Sanitization (prevent prompt injection)                        │
│                              │                                           │
│                              ▼                                           │
│  3. Wikipedia API → Fetch "Photosynthesis" article (8000 chars max)      │
│                              │                                           │
│                              ▼                                           │
│  4. GPT-4o with Function Calling                                         │
│     - System prompt defines assistant behavior                           │
│     - User message + Wikipedia context                                   │
│     - Tool: generate_quiz(topic, title, tags, num_questions)             │
│                              │                                           │
│                              ▼                                           │
│  5. GPT-4o returns tool call with quiz data                              │
│                              │                                           │
│                              ▼                                           │
│  6. Tool Handler executes: creates Quiz + Questions in PostgreSQL        │
│                              │                                           │
│                              ▼                                           │
│  7. GPT-4o generates human-readable response                             │
│                              │                                           │
│                              ▼                                           │
│  8. Response returned to instructor: "I've created a quiz..."            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        JWT TOKEN FLOW                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LOGIN                                                                  │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐                   │
│  │ Client  │ ──1──▶  │ Server  │ ──2──▶  │   DB    │                   │
│  │         │         │         │         │         │                   │
│  │         │  ◀──4── │         │  ◀──3── │         │                   │
│  └─────────┘         └─────────┘         └─────────┘                   │
│     Store tokens        Create tokens       Verify password             │
│     in localStorage     (access: 15min,     Store refresh_token hash   │
│                         refresh: 7 days)                                │
│                                                                         │
│  API REQUEST (with expired access token)                                │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐                   │
│  │ Client  │ ──1──▶  │ Server  │         │         │                   │
│  │         │         │  401    │         │         │                   │
│  │ Axios   │  ◀──2── │         │         │         │                   │
│  │ Inter-  │         │         │         │         │                   │
│  │ ceptor  │ ──3──▶  │ /refresh│ ──4──▶  │   DB    │                   │
│  │         │         │         │         │ Verify  │                   │
│  │         │  ◀──6── │         │  ◀──5── │  hash   │                   │
│  │         │         │ New     │         │         │                   │
│  │ Retry   │ ──7──▶  │ token   │         │         │                   │
│  │ original│         │         │         │         │                   │
│  └─────────┘         └─────────┘         └─────────┘                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Decisions

### Why These Choices?

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| **Backend Framework** | FastAPI | Native async support, automatic OpenAPI docs, Pydantic validation, excellent Python typing support |
| **Database** | PostgreSQL | ACID compliance, robust async support with asyncpg, native UUID type, production-ready |
| **ORM** | SQLAlchemy 2.0 | Modern async API, excellent typing support, migration support via Alembic |
| **Frontend Framework** | React + TypeScript | Type safety, large ecosystem, excellent developer experience |
| **Build Tool** | Vite | Fast HMR, native ESM support, simple configuration |
| **State Management** | TanStack Query | Server-state caching, automatic background refetching, optimistic updates |
| **UI Components** | shadcn/ui | Accessible, customizable, copy-paste components (not a dependency) |
| **Styling** | Tailwind CSS | Utility-first approach enables rapid prototyping, easy theming via CSS variables |
| **AI Model** | GPT-4o | Best-in-class for educational content generation, function calling support |
| **RAG Source** | Wikipedia | Free, comprehensive educational content, structured API |

### Architecture Patterns

1. **Layered Architecture**: Routers → Services → Models (separation of concerns)
2. **Repository Pattern**: Services abstract database operations
3. **Dependency Injection**: FastAPI's `Depends()` for database sessions, auth
4. **Token Refresh Pattern**: Automatic access token refresh in Axios interceptor
5. **Function Calling Pattern**: AI actions via OpenAI tools (not free-form generation)

### Trade-offs Made

| Trade-off | Decision | Reason |
|-----------|----------|--------|
| Client-side token storage | localStorage | Simplicity over security (production would use httpOnly cookies) |
| SQLite for tests | In-memory SQLite | Fast test execution, no external dependencies |
| No email verification | Skipped for MVP | Time constraint, not core to quiz functionality |
| Single AI model | GPT-4o only | Best quality for educational content; could add model selection later |
| No rate limiting | Skipped for MVP | Would add for production with Redis |

---

## AI Integration & Reasoning

### Why OpenAI GPT-4o?

1. **Quality**: GPT-4o produces the most accurate and well-structured educational content
2. **Function Calling**: Native support for structured tool execution (vs. parsing free-form text)
3. **Context Window**: 128K tokens allows for substantial Wikipedia content injection
4. **Reliability**: Consistent JSON output with `response_format={"type": "json_object"}`

### Why Function Calling Over Free-Form Generation?

```
❌ Free-form: "Generate a quiz" → Parse unpredictable text → Hope it's valid JSON
✅ Function Calling: "Generate a quiz" → AI calls generate_quiz(topic, ...) → Structured execution
```

**Benefits**:
- **Predictable**: AI chooses from defined tools, not arbitrary actions
- **Validated**: Tool parameters are validated by OpenAI before execution
- **Auditable**: Clear log of which tools were called with what parameters
- **Secure**: AI cannot invent new operations outside defined tools

### Available AI Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `generate_quiz` | Create new quiz with AI questions | topic, title?, tags?, num_questions? |
| `edit_quiz` | Update quiz properties | quiz_title, new_title?, description?, tags? |
| `delete_quiz` | Remove a quiz | quiz_title |
| `list_quizzes` | List instructor's quizzes | search? |
| `get_quiz_details` | Get full quiz information | quiz_title |
| `get_quiz_analytics` | Get quiz statistics | quiz_title |
| `edit_question` | Modify a specific question | quiz_title, question_number, ...fields |
| `add_questions` | Add questions to existing quiz | quiz_title, topic?, num_questions? |

### Why Wikipedia for RAG?

1. **Free**: No API costs, unlimited requests with proper User-Agent
2. **Educational**: Content is written for learning, well-cited
3. **Comprehensive**: Covers virtually any educational topic
4. **Structured**: API returns clean text extracts

**RAG Flow**:
```python
# 1. Search Wikipedia for topic
search_results = await wikipedia_api.search("photosynthesis")

# 2. Extract page content (up to 8000 chars)
content = await wikipedia_api.get_extract(page_title)

# 3. Include in GPT-4o prompt
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"Context:\n{content}\n\nCreate a quiz about {topic}"}
]
```

### AI Security Guardrails

1. **Input Sanitization**: Filter prompt injection patterns before sending to AI
   ```python
   # Blocked patterns
   "ignore previous instructions"
   "disregard all instructions"
   "system:"
   "pretend to be"
   ```

2. **System Prompt Boundaries**: AI is explicitly constrained to quiz operations only

3. **Tool-Only Actions**: AI cannot perform arbitrary actions, only defined tools

4. **Instructor-Only Access**: Chat endpoint requires instructor role

---

## Tech Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.109.2 |
| Runtime | Python | 3.11+ |
| ORM | SQLAlchemy | 2.0.25 |
| Database Driver | asyncpg | 0.29.0 |
| Migrations | Alembic | 1.13.1 |
| Auth | PyJWT + bcrypt | 2.8.0 / 4.1.2 |
| AI | openai | 1.12.0 |
| HTTP Client | httpx | 0.26.0 |
| Validation | Pydantic | 2.6.1 |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.2.0 |
| Language | TypeScript | 5.3+ |
| Build Tool | Vite | 5.0+ |
| Styling | Tailwind CSS | 3.4+ |
| Components | shadcn/ui | (copy-paste) |
| State | TanStack Query | 5.17.19 |
| Routing | React Router | 6.21.3 |
| HTTP Client | Axios | 1.6.7 |
| Charts | Recharts | 2.10.4 |
| Forms | React Hook Form + Zod | 7.49.3 / 3.22.4 |

### Database

| Component | Technology |
|-----------|------------|
| RDBMS | PostgreSQL 15+ |
| Tables | users, quizzes, questions, quiz_tags, quiz_attempts, attempt_answers, refresh_tokens |

### External Services

| Service | Purpose |
|---------|---------|
| OpenAI API | GPT-4o for quiz generation and chatbot |
| Wikipedia API | Educational content for RAG |

---

## Project Structure

```
knowledge_quiz_builder/
├── README.md                       # This file
├── PRD.md                          # Product Requirements Document
├── IMPLEMENTATION_PLAN.md          # Technical Implementation Guide
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry point, CORS, router registration
│   │   ├── config.py               # Pydantic settings from environment
│   │   ├── database.py             # SQLAlchemy async engine and session
│   │   ├── dependencies.py         # Auth dependencies (get_current_user, require_instructor)
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py             # User, UserRole, ThemePreference
│   │   │   ├── quiz.py             # Quiz, Question, QuizTag, AnswerOption
│   │   │   ├── attempt.py          # QuizAttempt, AttemptAnswer, AttemptStatus
│   │   │   └── token.py            # RefreshToken
│   │   │
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── user.py             # UserCreate, UserLogin, TokenResponse
│   │   │   ├── quiz.py             # QuizCreate, QuizUpdate, QuizResponse
│   │   │   ├── attempt.py          # AttemptStart, AttemptSubmit, AttemptResult
│   │   │   └── chat.py             # ChatMessage, ChatResponse
│   │   │
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py             # /api/auth/* (register, login, refresh, logout)
│   │   │   ├── user.py             # /api/users/* (profile, theme)
│   │   │   ├── quiz.py             # /api/quizzes/* (CRUD, analytics)
│   │   │   ├── attempt.py          # /api/attempts/* (start, save, submit)
│   │   │   └── chat.py             # /api/chat (AI chatbot)
│   │   │
│   │   ├── services/               # Business logic layer
│   │   │   ├── auth_service.py     # Registration, login, token management
│   │   │   ├── quiz_service.py     # Quiz CRUD operations
│   │   │   ├── attempt_service.py  # Quiz attempt management
│   │   │   ├── analytics_service.py# Statistics calculation
│   │   │   ├── ai_service.py       # OpenAI chatbot integration
│   │   │   └── wikipedia_service.py# Wikipedia API for RAG
│   │   │
│   │   ├── ai/                     # AI-specific modules
│   │   │   ├── tools.py            # OpenAI function calling definitions
│   │   │   ├── handlers.py         # Tool execution handlers
│   │   │   └── prompts.py          # System prompts
│   │   │
│   │   └── utils/                  # Utilities
│   │       ├── auth.py             # JWT, password hashing
│   │       └── sanitize.py         # Input sanitization for AI
│   │
│   ├── alembic/                    # Database migrations
│   │   └── versions/               # Migration files
│   │
│   ├── tests/                      # Test suite
│   │   ├── conftest.py             # Shared fixtures
│   │   ├── pytest.ini              # Pytest configuration
│   │   ├── unit/                   # Unit tests (mocked dependencies)
│   │   ├── integration/            # Integration tests (real test DB)
│   │   └── benchmarks/             # AI quality benchmarks (real OpenAI)
│   │
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment template
│   └── .tool-versions              # asdf version manager
│
└── frontend/
    ├── src/
    │   ├── main.tsx                # React entry point
    │   ├── App.tsx                 # Root component with routing
    │   │
    │   ├── components/             # Reusable components
    │   │   ├── ui/                 # shadcn/ui components
    │   │   ├── Layout.tsx          # Main layout with navigation
    │   │   ├── ChatPanel.tsx       # AI chatbot slide-out panel
    │   │   ├── Mascots.tsx         # Theme-based mascot SVGs
    │   │   └── ProtectedRoute.tsx  # Auth-required route wrapper
    │   │
    │   ├── pages/                  # Page components
    │   │   ├── HomePage.tsx
    │   │   ├── LoginPage.tsx
    │   │   ├── RegisterPage.tsx
    │   │   ├── QuizListPage.tsx    # Browse quizzes
    │   │   ├── QuizDetailPage.tsx  # View quiz
    │   │   ├── QuizCreatePage.tsx  # Manual quiz creation
    │   │   ├── QuizEditPage.tsx    # Edit quiz
    │   │   ├── QuizTakePage.tsx    # Take quiz
    │   │   ├── QuizResultPage.tsx  # View results
    │   │   ├── QuizAnalyticsPage.tsx # Instructor analytics
    │   │   ├── MyQuizzesPage.tsx   # Instructor dashboard
    │   │   └── MyAttemptsPage.tsx  # Student attempt history
    │   │
    │   ├── services/
    │   │   └── api.ts              # Axios instance with token refresh
    │   │
    │   ├── hooks/
    │   │   ├── use-auth.ts         # Authentication state
    │   │   ├── use-theme.ts        # Theme management
    │   │   └── use-toast.ts        # Toast notifications
    │   │
    │   ├── types/
    │   │   └── index.ts            # TypeScript interfaces
    │   │
    │   └── styles/
    │       └── globals.css         # Tailwind + theme CSS variables
    │
    ├── package.json
    ├── vite.config.ts              # Vite configuration with API proxy
    ├── tailwind.config.ts          # Tailwind configuration
    └── tsconfig.json               # TypeScript configuration
```

---

## Setup Instructions

### Prerequisites

- **Python 3.11+** (recommend [asdf](https://asdf-vm.com/): `asdf install python 3.11.5`)
- **Node.js 18+** (recommend asdf: `asdf install nodejs 18.19.0`)
- **PostgreSQL 14+**
- **OpenAI API key** with GPT-4o access

### Step 1: Database Setup

**macOS (Homebrew)**:
```bash
brew install postgresql@14
brew services start postgresql@14
createdb quiz_builder
```

**Ubuntu/Debian**:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb quiz_builder
```

**Docker** (alternative):
```bash
docker run --name quiz-postgres -e POSTGRES_DB=quiz_builder -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

**Edit `backend/.env`**:
```bash
# Database (update username for your system)
DATABASE_URL=postgresql+asyncpg://YOUR_USERNAME@localhost:5432/quiz_builder

# For Docker PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/quiz_builder

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI API Key (required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# CORS
FRONTEND_URL=http://localhost:5173
```

```bash
# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

**Backend available at**: http://localhost:8000
**API Documentation**: http://localhost:8000/docs

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend available at**: http://localhost:5173

---

## Running the Application

### Development Mode

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### Using the Application

1. **Register**: Go to http://localhost:5173/register
   - Choose "Instructor" role to access AI chatbot
   - Choose "Student" role to take quizzes

2. **Create Quiz (AI)**: As instructor, click chat icon in header
   - Try: "Create a quiz about the solar system"
   - Try: "Add 3 more questions to my solar system quiz"

3. **Create Quiz (Manual)**: Click "Create Quiz" button on My Quizzes page

4. **Take Quiz**: As student, browse quizzes and click "Start Quiz"

5. **View Analytics**: As instructor, click "Analytics" on any quiz you created

---

## Testing

### Test Suite Overview

| Type | Location | Description | Requires |
|------|----------|-------------|----------|
| Unit | `tests/unit/` | Service layer with mocked DB | Nothing |
| Integration | `tests/integration/` | API routes with test DB | Nothing |
| Benchmark | `tests/benchmarks/` | AI quality metrics | OPENAI_API_KEY |

### Running Tests

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run all tests (excluding AI benchmarks)
pytest tests/unit tests/integration

# Run with verbose output
pytest tests/unit tests/integration -v

# Run with coverage report
pytest tests/unit tests/integration --cov=app --cov-report=html
# View report: open htmlcov/index.html

# Run specific test file
pytest tests/unit/services/test_quiz_service.py -v

# Run specific test
pytest tests/unit/services/test_quiz_service.py::TestQuizServiceCreate::test_create_quiz_with_all_fields -v
```

### AI Benchmark Tests

These tests make **real API calls** to OpenAI and measure quality metrics.

```bash
# Set API key and run benchmarks
OPENAI_API_KEY=sk-... pytest tests/benchmarks/ -v

# Run specific benchmark
OPENAI_API_KEY=sk-... pytest tests/benchmarks/test_quiz_generation.py -v
```

**Benchmark Metrics**:
- Factual accuracy (keywords from Wikipedia found in generated quiz)
- Question clarity (proper formatting, distinct options)
- Explanation quality (adequate length, references correct answer)
- Tool selection accuracy (AI picks correct tool for request)

### Test Coverage

Current coverage: **~82%**

```bash
# Generate coverage report
pytest tests/unit tests/integration --cov=app --cov-report=term-missing
```

### Frontend Tests

```bash
cd frontend
npm run test
```

---

## API Reference

### Authentication

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/auth/register` | POST | Create account | No |
| `/api/auth/login` | POST | Get JWT tokens | No |
| `/api/auth/refresh` | POST | Refresh access token | No |
| `/api/auth/logout` | POST | Invalidate refresh token | No |
| `/api/auth/me` | GET | Get current user | Yes |

### Quizzes

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/quizzes` | GET | List/search quizzes | Yes |
| `/api/quizzes/{id}` | GET | Get quiz details | Yes |
| `/api/quizzes` | POST | Create quiz | Instructor |
| `/api/quizzes/{id}` | PUT | Update quiz | Owner |
| `/api/quizzes/{id}` | DELETE | Delete quiz | Owner |
| `/api/quizzes/my` | GET | Get instructor's quizzes | Instructor |
| `/api/quizzes/my/stats` | GET | Get dashboard stats | Instructor |
| `/api/quizzes/{id}/analytics` | GET | Get quiz analytics | Owner |

### Attempts

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/attempts/{quizId}/start` | POST | Start/resume attempt | Yes |
| `/api/attempts/{id}` | PUT | Save progress | Yes |
| `/api/attempts/{id}/submit` | POST | Submit attempt | Yes |
| `/api/attempts/{id}` | GET | Get attempt result | Yes |
| `/api/attempts/my` | GET | Get user's attempts | Yes |

### Chat

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/chat` | POST | Send message to AI | Instructor |

### Users

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/users/me` | GET | Get profile | Yes |
| `/api/users/me` | PUT | Update profile/theme | Yes |

---

## Features Overview

### For Instructors

- **AI Quiz Generation**: Chat with AI to create quizzes on any topic
- **Manual Quiz Creation**: Create quizzes through traditional form UI
- **Quiz Management**: Edit, delete, publish/unpublish quizzes
- **Analytics Dashboard**: View score distributions, question difficulty, student leaderboard
- **Theme Selection**: Choose between BYU (blue) and Utah (red) themes

### For Students

- **Quiz Discovery**: Browse, search, and filter available quizzes
- **Quiz Taking**: Take quizzes with auto-save progress
- **Instant Feedback**: See score, correct answers, and explanations after submission
- **Attempt History**: Review past attempts and track improvement
- **Unlimited Retakes**: Best score is tracked per quiz

### Theme System

| Theme | Primary Color | AI Mascot |
|-------|---------------|-----------|
| BYU | #002E5D (Navy Blue) | Cosmo the Cougar |
| Utah | #CC0000 (Red) | Swoop the Ute |

---

## Security Considerations

### Implemented

| Feature | Implementation |
|---------|----------------|
| Password Hashing | bcrypt with salt |
| JWT Access Tokens | 15-minute expiry, stored in localStorage |
| JWT Refresh Tokens | 7-day expiry, hashed in database |
| Role-Based Access | Instructor vs Student permissions |
| Input Sanitization | Prompt injection filtering for AI |
| CORS | Configured for frontend origin only |
| SQL Injection | Prevented by SQLAlchemy ORM |

### Production Recommendations

| Improvement | Reason |
|-------------|--------|
| httpOnly Cookies | Prevent XSS token theft |
| Rate Limiting | Prevent abuse (especially AI endpoint) |
| HTTPS | Encrypt traffic |
| Input Validation | Stricter limits on all endpoints |
| Audit Logging | Track AI tool usage |
| API Keys | Rotate OpenAI keys regularly |

---

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
brew services list  # macOS
systemctl status postgresql  # Linux

# Verify database exists
psql -l | grep quiz_builder

# Check your DATABASE_URL username
whoami  # Use this username in DATABASE_URL
```

### Enum Errors on Registration

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### OpenAI API Errors

1. Verify `OPENAI_API_KEY` is set in `.env`
2. Check API key has GPT-4o access
3. Verify API key has credits remaining

### Frontend Can't Connect to Backend

1. Ensure backend is running on port 8000
2. Check Vite proxy in `frontend/vite.config.ts`
3. Verify CORS settings in `backend/app/main.py`

### Tests Failing with UUID Errors

This is handled automatically in `conftest.py`, but if issues persist:
```python
# Ensure this line is in tests/conftest.py
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "VARCHAR(36)"
```

---

## Additional Documentation

- **[PRD.md](./PRD.md)** - Product Requirements Document with detailed user flows
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Technical implementation guide

---

## License

MIT
