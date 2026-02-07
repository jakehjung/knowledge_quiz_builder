import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  TokenResponse,
  User,
  Quiz,
  QuizListResponse,
  QuizCreate,
  QuizUpdate,
  Attempt,
  AttemptResult,
  UserAttemptsResponse,
  QuizAnalytics,
  ChatResponse,
  AnswerOption,
  ThemePreference,
} from '@/types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const response = await axios.post<{ access_token: string }>(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    role: 'instructor' | 'student';
    display_name?: string;
  }): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', { email, password });
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await api.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  logout: async (): Promise<void> => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// User API
export const userApi = {
  getProfile: async (): Promise<User> => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  updateProfile: async (data: {
    display_name?: string;
    theme_preference?: ThemePreference;
  }): Promise<User> => {
    const response = await api.put<User>('/users/me', data);
    return response.data;
  },
};

// Quiz API
export const quizApi = {
  list: async (params?: {
    search?: string;
    tags?: string[];
    sort?: 'newest' | 'oldest' | 'alphabetical' | 'popular';
    page?: number;
    page_size?: number;
  }): Promise<QuizListResponse> => {
    const response = await api.get<QuizListResponse>('/quizzes', { params });
    return response.data;
  },

  get: async (id: string): Promise<Quiz> => {
    const response = await api.get<Quiz>(`/quizzes/${id}`);
    return response.data;
  },

  create: async (data: QuizCreate): Promise<Quiz> => {
    const response = await api.post<Quiz>('/quizzes', data);
    return response.data;
  },

  update: async (id: string, data: QuizUpdate): Promise<Quiz> => {
    const response = await api.put<Quiz>(`/quizzes/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/quizzes/${id}`);
  },

  getAnalytics: async (id: string): Promise<QuizAnalytics> => {
    const response = await api.get<QuizAnalytics>(`/quizzes/${id}/analytics`);
    return response.data;
  },

  getMyQuizzes: async (): Promise<QuizListResponse> => {
    const response = await api.get<QuizListResponse>('/quizzes/my');
    return response.data;
  },

  getMyStats: async (): Promise<{
    total_quizzes: number;
    total_students: number;
    total_attempts: number;
    average_percentage: number;
  }> => {
    const response = await api.get('/quizzes/my/stats');
    return response.data;
  },
};

// Attempt API
export const attemptApi = {
  start: async (quizId: string): Promise<Attempt> => {
    const response = await api.post<Attempt>(`/attempts/${quizId}/start`);
    return response.data;
  },

  saveProgress: async (
    attemptId: string,
    answers: { question_id: string; selected_answer: AnswerOption | null }[]
  ): Promise<Attempt> => {
    const response = await api.put<Attempt>(`/attempts/${attemptId}`, { answers });
    return response.data;
  },

  submit: async (
    attemptId: string,
    answers: { question_id: string; selected_answer: AnswerOption | null }[]
  ): Promise<AttemptResult> => {
    const response = await api.post<AttemptResult>(`/attempts/${attemptId}/submit`, { answers });
    return response.data;
  },

  get: async (attemptId: string): Promise<AttemptResult> => {
    const response = await api.get<AttemptResult>(`/attempts/${attemptId}`);
    return response.data;
  },

  getMyAttempts: async (): Promise<UserAttemptsResponse> => {
    const response = await api.get<UserAttemptsResponse>('/attempts/my');
    return response.data;
  },
};

// Chat API
export const chatApi = {
  send: async (
    message: string,
    conversationHistory?: { role: string; content: string }[]
  ): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', {
      message,
      conversation_history: conversationHistory,
    });
    return response.data;
  },
};

export default api;
