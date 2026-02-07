# AI-Powered Knowledge Quiz Builder
## Product Requirements Document (PRD)

---

## Executive Summary

The **AI-Powered Knowledge Quiz Builder** is a full-stack web application that enables educational institutions to create, manage, and administer multiple-choice quizzes with AI assistance. The platform supports two user roles: **Instructors** who create and manage quizzes, and **Students** who take quizzes and track their progress.

### Key Differentiators

1. **AI-Powered Quiz Generation**: Instructors can generate complete quizzes by simply providing a topic. The AI uses Wikipedia as a knowledge source (RAG) to ensure factual accuracy.

2. **Conversational AI Assistant**: A themed chatbot (mascot-based) allows instructors to manage quizzes through natural language conversations, supporting quiz creation, editing, deletion, and analytics queries.

3. **University Theme System**: The application supports customizable themes representing different universities (BYU Blue and Utah Red), with themed AI mascots (Cosmo the Cougar and Swoop the Ute).

4. **Comprehensive Analytics**: Instructors receive detailed analytics including score distributions, question difficulty analysis, and student leaderboards.

5. **Progress Preservation**: Students can close their browser mid-quiz and resume exactly where they left off.

### Technical Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vite + React 18 + TypeScript |
| UI Components | Tailwind CSS + shadcn/ui |
| State Management | TanStack Query (React Query) |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 (async) |
| AI | OpenAI GPT-4o with Function Calling |
| RAG | Wikipedia API |
| Authentication | JWT (access + refresh tokens) |

---

## Table of Contents

1. [User Roles & Permissions](#1-user-roles--permissions)
2. [User Experience Flows](#2-user-experience-flows)
3. [Feature Specifications](#3-feature-specifications)
4. [Data Models](#4-data-models)
5. [API Endpoints](#5-api-endpoints)
6. [AI Integration](#6-ai-integration)
7. [Security Requirements](#7-security-requirements)
8. [Theme System](#8-theme-system)
9. [Out of Scope](#9-out-of-scope)

---

## 1. User Roles & Permissions

### 1.1 Role Definitions

| Role | Description |
|------|-------------|
| **Instructor** | Creates and manages quizzes, views analytics, uses AI chatbot |
| **Student** | Browses quizzes, takes quizzes, views own scores and history |

### 1.2 Permission Matrix

| Feature | Instructor | Student | Unauthenticated |
|---------|:----------:|:-------:|:---------------:|
| Register/Login | ✅ | ✅ | ✅ |
| Browse Published Quizzes | ✅ | ✅ | ❌ |
| View Quiz Details | ✅ (with answers) | ✅ (without answers) | ❌ |
| Create Quiz (Manual) | ✅ | ❌ | ❌ |
| Create Quiz (AI) | ✅ | ❌ | ❌ |
| Edit Quiz | ✅ (own only) | ❌ | ❌ |
| Delete Quiz | ✅ (own only) | ❌ | ❌ |
| View Quiz Analytics | ✅ (own only) | ❌ | ❌ |
| Access AI Chatbot | ✅ | ❌ | ❌ |
| Take Quiz | ✅ | ✅ | ❌ |
| View Own Attempt History | ✅ | ✅ | ❌ |
| Change Theme | ✅ | ✅ | ❌ |

---

## 2. User Experience Flows

### 2.1 Registration Flow

**Entry Point**: User navigates to `/register`

**Steps**:
1. User sees registration form with fields:
   - Email address (required, validated format)
   - Password (required, min 8 chars, 1 number, 1 special character)
   - Display name (optional)
   - Role selection (radio buttons: Instructor or Student)
2. User fills form and clicks "Create Account"
3. System validates input:
   - If email already exists → Show error: "Email already registered"
   - If password too weak → Show inline validation errors
4. On success:
   - System creates user account
   - System generates JWT access token (15 min) and refresh token (7 days)
   - User is redirected to home page
   - Toast notification: "Account created successfully"

**Visual States**:
- Loading state with spinner during submission
- Error states with red border on invalid fields
- Success redirect with toast notification

---

### 2.2 Login Flow

**Entry Point**: User navigates to `/login`

**Steps**:
1. User sees login form with:
   - Email address field
   - Password field
   - "Create account" link
2. User enters credentials and clicks "Sign In"
3. System validates:
   - If credentials invalid → Show error: "Invalid email or password"
4. On success:
   - System stores tokens in localStorage
   - User is redirected to home page
   - If instructor: AI chatbot button appears in header

**Token Refresh Behavior**:
- Access token expires in 15 minutes
- When API returns 401, system automatically attempts refresh
- If refresh succeeds, original request is retried transparently
- If refresh fails, user is redirected to login page

---

### 2.3 Quiz Discovery Flow (Student)

**Entry Point**: Student clicks "Browse Quizzes" or navigates to `/quizzes`

**Page Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  [Search: ______________]  [Sort: Newest ▼]                │
│                                                             │
│  Popular Tags: [Python] [History] [Science] [Math]         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ 📚 Quiz Title       │  │ 📚 Quiz Title       │          │
│  │ Topic: Biology      │  │ Topic: Chemistry    │          │
│  │ 5 questions         │  │ 5 questions         │          │
│  │ By: Prof. Smith     │  │ By: Prof. Jones     │          │
│  │ [Start Quiz]        │  │ [Start Quiz]        │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ◀ Page 1 of 5 ▶                                           │
└─────────────────────────────────────────────────────────────┘
```

**Interactions**:
1. **Search**: Type in search box → Filters by title, description, topic
2. **Sort Options**: Newest, Oldest, Alphabetical, Popular (by attempt count)
3. **Tag Filter**: Click tag → Filters to quizzes with that tag
4. **Start Quiz**: Click → Navigate to `/quizzes/{id}/take`

**Empty States**:
- No quizzes found: "No quizzes match your search. Try different keywords."
- No quizzes exist: "No quizzes available yet. Check back soon!"

---

### 2.4 Quiz Taking Flow (Student)

**Entry Point**: Student clicks "Start Quiz" on a quiz card

**Pre-Quiz State**:
1. System calls `POST /api/attempts/{quizId}/start`
2. If existing in-progress attempt exists → Resume that attempt
3. If no existing attempt → Create new attempt with empty answers

**Quiz Interface**:
```
┌─────────────────────────────────────────────────────────────┐
│  Introduction to Python                                     │
│  Question 2 of 5                    [2 answered]           │
│  ████████████░░░░░░░░░░░░ 40%                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What is the correct way to declare a variable in Python?  │
│                                                             │
│  ○ A. var x = 5                                            │
│  ● B. x = 5                                                │
│  ○ C. int x = 5                                            │
│  ○ D. declare x = 5                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [◀ Previous]                               [Next ▶]       │
│                                                             │
│  Question Navigator: [1] [2] [3] [4] [5]                   │
└─────────────────────────────────────────────────────────────┘
```

**Behaviors**:

1. **Selecting Answer**:
   - Click radio button → Answer is highlighted
   - System immediately calls `PUT /api/attempts/{id}` to save progress
   - Question navigator button turns filled (answered) or outlined (unanswered)

2. **Navigation**:
   - "Previous" / "Next" buttons to move between questions
   - Question navigator allows jumping to any question
   - Current question is highlighted in navigator

3. **Progress Saving**:
   - Every answer selection triggers auto-save
   - User can close browser and return later
   - On return: `POST /api/attempts/{quizId}/start` returns existing attempt with saved answers

4. **Submission**:
   - On last question, "Next" becomes "Submit Quiz"
   - If not all questions answered → Toast: "Please answer all questions"
   - On submit → `POST /api/attempts/{id}/submit`
   - Redirect to results page

---

### 2.5 Quiz Results Flow

**Entry Point**: After submitting quiz or viewing past attempt

**Results Page**:
```
┌─────────────────────────────────────────────────────────────┐
│                        🏆                                   │
│                       4/5                                   │
│                    80% Correct                              │
│               Introduction to Python                        │
│                                                             │
│        [View Quiz]  [Retake Quiz]                          │
├─────────────────────────────────────────────────────────────┤
│  Review Your Answers                                        │
│                                                             │
│  ✅ 1. What is Python?                                     │
│     ┌─────────────────────────────────────────────────┐    │
│     │ A. A snake                                       │    │
│     │ ✓ B. A programming language (Correct Answer)    │    │
│     │ C. A database                                    │    │
│     │ D. An operating system                          │    │
│     ├─────────────────────────────────────────────────┤    │
│     │ 💡 Explanation: Python is a high-level...       │    │
│     └─────────────────────────────────────────────────┘    │
│                                                             │
│  ❌ 2. What is a list in Python?                           │
│     ┌─────────────────────────────────────────────────┐    │
│     │ ✗ A. A function (Your Answer)                   │    │
│     │ ✓ B. A data structure (Correct Answer)          │    │
│     │ C. A loop                                        │    │
│     │ D. A class                                       │    │
│     ├─────────────────────────────────────────────────┤    │
│     │ 💡 Explanation: A list is a mutable...          │    │
│     └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Score displayed prominently with trophy icon
- Pass/fail coloring (green ≥60%, red <60%)
- Each question shows:
  - Correct/incorrect indicator
  - All options with correct answer highlighted in green
  - User's wrong answer highlighted in red (if applicable)
  - AI-generated explanation
- "Retake Quiz" starts a fresh attempt

---

### 2.6 Instructor Dashboard Flow

**Entry Point**: Instructor clicks "My Quizzes" in navigation

**Dashboard Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  My Dashboard                                               │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 12 Quizzes   │ │ 156 Students │ │ 423 Attempts │        │
│  │ Total        │ │ Unique       │ │ Total        │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌──────────────┐                                          │
│  │ 78.5%        │                                          │
│  │ Avg Score    │                                          │
│  └──────────────┘                                          │
├─────────────────────────────────────────────────────────────┤
│  My Quizzes                              [+ Create Quiz]   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📚 Python Basics                                     │   │
│  │ Topic: Programming │ 45 attempts │ Created: Jan 15  │   │
│  │ [Edit] [Analytics] [Delete]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📚 World History                                     │   │
│  │ Topic: History │ 23 attempts │ Created: Jan 10      │   │
│  │ [Edit] [Analytics] [Delete]                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Statistics Calculated**:
- Total Quizzes: Count of instructor's quizzes
- Unique Students: Distinct users who attempted any quiz (excluding instructor)
- Total Attempts: All completed attempts across all quizzes
- Average Score: Mean percentage across all attempts

---

### 2.7 Quiz Creation Flow (Manual)

**Entry Point**: Instructor clicks "+ Create Quiz" button

**Step 1: Quiz Details**
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Quiz                                            │
│                                                             │
│  Title: [____________________________________]              │
│  Description: [____________________________________]        │
│  Topic: [____________________________________]              │
│  Tags: [python] [programming] [+Add]                        │
└─────────────────────────────────────────────────────────────┘
```

**Step 2: Add Questions**
```
┌─────────────────────────────────────────────────────────────┐
│  Question 1 of 5                                            │
│                                                             │
│  Question: [____________________________________]           │
│                                                             │
│  Option A: [____________________________________]           │
│  Option B: [____________________________________]           │
│  Option C: [____________________________________]           │
│  Option D: [____________________________________]           │
│                                                             │
│  Correct Answer: ○A ○B ○C ●D                               │
│                                                             │
│  Explanation (optional):                                    │
│  [____________________________________]                     │
│                                                             │
│  [Previous Question] [Next Question] [+ Add Question]      │
└─────────────────────────────────────────────────────────────┘
```

**Validation Rules**:
- Title: Required, max 200 characters
- Description: Optional, max 1000 characters
- Topic: Required
- Questions: Minimum 1, each must have all 4 options filled
- Correct answer: Must be selected for each question

**On Submit**:
- Quiz is created with `is_published = true` (auto-published)
- Redirect to quiz detail page
- Toast: "Quiz created successfully"

---

### 2.8 Quiz Creation Flow (AI Chatbot)

**Entry Point**: Instructor clicks chat icon in header (only visible to instructors)

**Chat Panel** (slides in from right):
```
┌─────────────────────────────────────────────────────────────┐
│  🐆 Cosmo the Cougar                              [✕]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🐆 Hi! I'm Cosmo the Cougar. I can help you create and   │
│     manage quizzes. Try asking me to:                       │
│     • Create a quiz about a topic                          │
│     • List your quizzes                                     │
│     • Show quiz analytics                                   │
│     • Edit or delete a quiz                                 │
│                                                             │
│  👤 Create a quiz about the French Revolution              │
│                                                             │
│  🐆 I'll create a quiz about the French Revolution for    │
│     you. Let me search for accurate information...         │
│                                                             │
│     [typing indicator: ...]                                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [Type a message...                        ] [Send →]      │
└─────────────────────────────────────────────────────────────┘
```

**AI Capabilities**:

| Command Example | Action |
|-----------------|--------|
| "Create a quiz about photosynthesis" | Generates 5-question quiz using Wikipedia RAG |
| "Make a 3-question quiz on World War 2" | Generates specified number of questions |
| "List my quizzes" | Shows instructor's quizzes with titles |
| "Show analytics for Python Basics" | Displays quiz statistics |
| "Edit the title of Python Basics to Python Fundamentals" | Updates quiz title |
| "Delete the quiz called Test Quiz" | Deletes specified quiz |
| "Add 2 more questions to Python Basics" | Adds questions to existing quiz |
| "Change question 3's correct answer to B" | Edits specific question |

**AI Personality by Theme**:
- **BYU Theme**: Cosmo the Cougar (friendly, encouraging)
- **Utah Theme**: Swoop the Ute (enthusiastic, supportive)

---

### 2.9 Quiz Analytics Flow

**Entry Point**: Instructor clicks "Analytics" on their quiz

**Analytics Dashboard**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Quiz                                             │
│                                                             │
│  Python Basics - Analytics                                  │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 45       │ │ 32       │ │ 3.8/5    │ │ 72%      │      │
│  │ Attempts │ │ Students │ │ Avg Score│ │ Pass Rate│      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│  Score Distribution          │  Question Difficulty        │
│  ┌───────────────────────┐  │  Q1: ████████████░░ 85%    │
│  │     ▓▓▓▓              │  │  Q2: ██████████░░░░ 70%    │
│  │   ▓▓▓▓▓▓▓▓            │  │  Q3: ████████░░░░░░ 55%    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓          │  │  Q4: ██████████████ 95%    │
│  │ 0  1  2  3  4  5      │  │  Q5: ████████████░░ 80%    │
│  └───────────────────────┘  │                             │
├─────────────────────────────────────────────────────────────┤
│  Student Leaderboard                                        │
│  1. John Smith          5/5    (2 attempts)                │
│  2. Jane Doe           4/5    (1 attempt)                  │
│  3. Bob Johnson        4/5    (3 attempts)                 │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

**Metrics Explained**:
- **Total Attempts**: All completed submissions
- **Unique Students**: Distinct users (instructor's own attempts excluded)
- **Average Score**: Mean score across all attempts
- **Pass Rate**: Percentage of attempts scoring ≥60%
- **Score Distribution**: Bar chart showing count of each score (0-5)
- **Question Difficulty**: Accuracy rate per question (helps identify hard questions)
- **Leaderboard**: Top 10 students by best score

---

### 2.10 Theme Switching Flow

**Entry Point**: User clicks theme toggle in header

**Behavior**:
1. User clicks sun/moon icon or theme selector
2. Theme immediately switches (CSS variables update)
3. System calls `PUT /api/users/me` with new theme preference
4. Theme persists across sessions

**Theme Specifications**:

| Theme | Primary Color | Secondary | AI Mascot |
|-------|--------------|-----------|-----------|
| BYU | #002E5D (Navy Blue) | #FFFFFF | Cosmo the Cougar |
| Utah | #CC0000 (Red) | #FFFFFF | Swoop the Ute |

---

## 3. Feature Specifications

### 3.1 Quiz Properties

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| id | UUID | Auto-generated | Unique identifier |
| title | string | Required, max 200 chars | Quiz title |
| description | string | Optional, max 1000 chars | Quiz description |
| topic | string | Required | Subject area for categorization |
| tags | string[] | Optional | Searchable tags |
| is_published | boolean | Default: true | Visibility status |
| instructor_id | UUID | Required | Creator reference |
| created_at | timestamp | Auto-set | Creation time |
| updated_at | timestamp | Auto-updated | Last modification |

### 3.2 Question Properties

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| id | UUID | Auto-generated | Unique identifier |
| quiz_id | UUID | Required | Parent quiz reference |
| question_text | string | Required | The question |
| option_a | string | Required | First option |
| option_b | string | Required | Second option |
| option_c | string | Required | Third option |
| option_d | string | Required | Fourth option |
| correct_answer | enum | A, B, C, or D | Correct option |
| explanation | string | Optional | AI-generated explanation |
| order_index | integer | Required | Display order |

### 3.3 Quiz Attempt Properties

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| id | UUID | Auto-generated | Unique identifier |
| quiz_id | UUID | Required | Quiz reference |
| user_id | UUID | Required | Student reference |
| status | enum | in_progress, completed | Attempt state |
| score | integer | Null until completed | Correct answers count |
| started_at | timestamp | Auto-set | Start time |
| completed_at | timestamp | Set on submit | Completion time |

### 3.4 Attempt Rules

1. **Starting**: Creating a new attempt or resuming existing in-progress attempt
2. **Progress Saving**: Answers saved immediately on selection
3. **Submission**: Calculates score, marks as completed
4. **Retakes**: Unlimited, each creates new attempt
5. **Best Score**: Analytics show best score per student

---

## 4. Data Models

### 4.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     users       │       │  refresh_tokens │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───────│ user_id (FK)    │
│ email           │       │ token_hash      │
│ password_hash   │       │ expires_at      │
│ role            │       │ created_at      │
│ display_name    │       └─────────────────┘
│ theme_preference│
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐       ┌─────────────────┐
│    quizzes      │───────│    quiz_tags    │
├─────────────────┤ 1:N   ├─────────────────┤
│ id (PK)         │       │ quiz_id (FK,PK) │
│ title           │       │ tag (PK)        │
│ description     │       └─────────────────┘
│ topic           │
│ instructor_id   │
│ is_published    │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│   questions     │
├─────────────────┤
│ id (PK)         │
│ quiz_id (FK)    │
│ question_text   │
│ option_a-d      │
│ correct_answer  │
│ explanation     │
│ order_index     │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐       ┌─────────────────┐
│  quiz_attempts  │───────│ attempt_answers │
├─────────────────┤ 1:N   ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ quiz_id (FK)    │       │ attempt_id (FK) │
│ user_id (FK)    │       │ question_id (FK)│
│ status          │       │ selected_answer │
│ score           │       │ is_correct      │
│ started_at      │       └─────────────────┘
│ completed_at    │
└─────────────────┘
```

---

## 5. API Endpoints

### 5.1 Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/register | Create account | No |
| POST | /api/auth/login | Get tokens | No |
| POST | /api/auth/refresh | Refresh access token | No |
| POST | /api/auth/logout | Invalidate refresh token | No |
| GET | /api/auth/me | Get current user | Yes |

### 5.2 User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/users/me | Get profile | Yes |
| PUT | /api/users/me | Update profile/theme | Yes |

### 5.3 Quiz Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/quizzes | List/search quizzes | Yes |
| GET | /api/quizzes/{id} | Get quiz details | Yes |
| POST | /api/quizzes | Create quiz | Instructor |
| PUT | /api/quizzes/{id} | Update quiz | Instructor (owner) |
| DELETE | /api/quizzes/{id} | Delete quiz | Instructor (owner) |
| GET | /api/quizzes/my | Get instructor's quizzes | Instructor |
| GET | /api/quizzes/my/stats | Get dashboard stats | Instructor |
| GET | /api/quizzes/{id}/analytics | Get quiz analytics | Instructor (owner) |

### 5.4 Quiz Attempts

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/attempts/{quizId}/start | Start/resume attempt | Yes |
| PUT | /api/attempts/{attemptId} | Save progress | Yes |
| POST | /api/attempts/{attemptId}/submit | Submit attempt | Yes |
| GET | /api/attempts/{attemptId} | Get attempt result | Yes |
| GET | /api/attempts/my | Get user's attempts | Yes |

### 5.5 AI Chat

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/chat | Send message to AI | Instructor |

---

## 6. AI Integration

### 6.1 OpenAI Function Calling Tools

The AI chatbot uses OpenAI's function calling feature with these tools:

| Tool | Parameters | Description |
|------|------------|-------------|
| `generate_quiz` | topic, title?, tags?, num_questions? | Create new quiz with AI questions |
| `edit_quiz` | quiz_title, new_title?, description?, tags? | Update quiz properties |
| `delete_quiz` | quiz_title | Delete a quiz |
| `list_quizzes` | search? | List instructor's quizzes |
| `get_quiz_details` | quiz_title | Get full quiz information |
| `get_quiz_analytics` | quiz_title | Get quiz statistics |
| `edit_question` | quiz_title, question_number, ...fields | Edit specific question |
| `add_questions` | quiz_title, topic?, num_questions? | Add questions to existing quiz |

### 6.2 RAG Integration (Wikipedia)

**Quiz Generation Flow**:
1. Instructor requests quiz on topic (e.g., "Photosynthesis")
2. System queries Wikipedia API for topic
3. Extracts up to 8,000 characters of content
4. GPT-4o generates questions using Wikipedia content as context
5. Questions include factually accurate information with explanations

### 6.3 Security Guardrails

**Input Sanitization**:
- HTML escape to prevent XSS
- Filter prompt injection patterns:
  - "ignore previous instructions"
  - "disregard all instructions"
  - "system:" role injection attempts
  - "pretend to be" role changes

**System Prompt Boundaries**:
- Assistant can only perform quiz operations
- Cannot access other users' data
- Cannot modify system settings
- References quizzes by title, not UUID (user-friendly)

---

## 7. Security Requirements

### 7.1 Authentication Security

| Requirement | Implementation |
|-------------|----------------|
| Password Hashing | bcrypt with salt |
| Access Token | JWT, 15-minute expiry |
| Refresh Token | 7-day expiry, hashed in database |
| Token Storage | localStorage (access + refresh) |

### 7.2 Authorization

| Resource | Rule |
|----------|------|
| Quiz Edit/Delete | Only owner instructor |
| Quiz Analytics | Only owner instructor |
| AI Chatbot | Only instructors |
| Quiz Details | Instructors see answers, students don't |

### 7.3 Input Validation

- Email format validation
- Password strength requirements (8+ chars, 1 number, 1 special)
- Quiz title max 200 characters
- Description max 1000 characters
- Question options all required

---

## 8. Theme System

### 8.1 CSS Variables

**BYU Theme**:
```css
--primary: 222.2 47.4% 11.2%;     /* Navy Blue */
--primary-foreground: 0 0% 100%;  /* White */
```

**Utah Theme**:
```css
--primary: 0 100% 40%;            /* Red */
--primary-foreground: 0 0% 100%;  /* White */
```

### 8.2 Theme-Aware Components

- Navigation header
- Buttons and links
- Progress bars
- Cards and badges
- AI chatbot mascot and panel header

---

## 9. Out of Scope

The following features are explicitly **not included** in this MVP:

- Course/class organization
- Time limits on quizzes
- Question randomization
- Admin panel for user management
- Email verification
- Password reset flow
- Mobile native apps
- Real-time collaboration
- Quiz versioning/history
- Bulk import/export of quizzes
- Custom question types (only multiple choice)
- Rich text/images in questions
- Grading curves or weighted scoring
- LTI integration with LMS platforms
