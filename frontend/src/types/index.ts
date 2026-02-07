export type UserRole = 'instructor' | 'student';
export type ThemePreference = 'byu' | 'utah';
export type AnswerOption = 'A' | 'B' | 'C' | 'D';
export type AttemptStatus = 'in_progress' | 'completed';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  display_name: string | null;
  theme_preference: ThemePreference;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Question {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer?: AnswerOption; // Only returned for instructors viewing their own quiz
  explanation?: string | null; // Only returned for instructors viewing their own quiz
  order_index: number;
}

export interface QuestionCreate {
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: AnswerOption;
  explanation?: string;
}

export interface QuizInstructor {
  id: string;
  display_name: string | null;
  email: string;
}

export interface Quiz {
  id: string;
  title: string;
  description: string | null;
  topic: string;
  tags: string[];
  questions: Question[];
  instructor: QuizInstructor;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuizListItem {
  id: string;
  title: string;
  description: string | null;
  topic: string;
  tags: string[];
  instructor: QuizInstructor;
  is_published: boolean;
  created_at: string;
  question_count: number;
}

export interface QuizListResponse {
  quizzes: QuizListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface QuizCreate {
  title: string;
  description?: string;
  topic: string;
  tags?: string[];
  questions: QuestionCreate[];
}

export interface QuizUpdate {
  title?: string;
  description?: string;
  topic?: string;
  tags?: string[];
  is_published?: boolean;
  questions?: QuestionCreate[];
}

export interface AttemptAnswer {
  question_id: string;
  selected_answer: AnswerOption | null;
  is_correct: boolean | null;
}

export interface Attempt {
  id: string;
  quiz_id: string;
  status: AttemptStatus;
  score: number | null;
  started_at: string;
  completed_at: string | null;
  answers: AttemptAnswer[];
}

export interface QuestionResult {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: AnswerOption;
  explanation: string | null;
  selected_answer: AnswerOption | null;
  is_correct: boolean | null;
}

export interface AttemptResult {
  id: string;
  quiz_id: string;
  quiz_title: string;
  status: AttemptStatus;
  score: number | null;
  total_questions: number;
  started_at: string;
  completed_at: string | null;
  questions: QuestionResult[];
}

export interface AttemptSummary {
  id: string;
  quiz_id: string;
  quiz_title: string;
  status: AttemptStatus;
  score: number | null;
  total_questions: number;
  started_at: string;
  completed_at: string | null;
}

export interface UserAttemptsResponse {
  attempts: AttemptSummary[];
  total: number;
}

export interface QuizAnalytics {
  quiz_id: string;
  quiz_title: string;
  total_questions: number;
  total_attempts: number;
  unique_students: number;
  average_score: number;
  score_distribution: Record<number, number>;
  question_analysis: QuestionAnalysis[];
  student_scores: StudentScore[];
}

export interface QuestionAnalysis {
  question_id: string;
  question_text: string;
  correct_count: number;
  incorrect_count: number;
  accuracy_rate: number;
}

export interface StudentScore {
  user_id: string;
  display_name: string | null;
  email: string;
  best_score: number;
  attempts_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  action_taken: string | null;
  data: unknown;
}
