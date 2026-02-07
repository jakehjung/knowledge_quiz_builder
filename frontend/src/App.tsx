import { Routes, Route } from 'react-router-dom';
import { ProtectedRoute, PublicOnlyRoute } from '@/components/RouteGuards';
import Layout from '@/components/Layout';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import HomePage from '@/pages/HomePage';
import QuizListPage from '@/pages/QuizListPage';
import QuizDetailPage from '@/pages/QuizDetailPage';
import QuizTakePage from '@/pages/QuizTakePage';
import QuizResultPage from '@/pages/QuizResultPage';
import QuizCreatePage from '@/pages/QuizCreatePage';
import QuizEditPage from '@/pages/QuizEditPage';
import QuizAnalyticsPage from '@/pages/QuizAnalyticsPage';
import MyQuizzesPage from '@/pages/MyQuizzesPage';
import MyAttemptsPage from '@/pages/MyAttemptsPage';

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        }
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="quizzes" element={<QuizListPage />} />
        <Route path="quizzes/create" element={<QuizCreatePage />} />
        <Route path="quizzes/:id" element={<QuizDetailPage />} />
        <Route path="quizzes/:id/edit" element={<QuizEditPage />} />
        <Route path="quizzes/:id/take" element={<QuizTakePage />} />
        <Route path="quizzes/:id/analytics" element={<QuizAnalyticsPage />} />
        <Route path="attempts/:attemptId/result" element={<QuizResultPage />} />
        <Route path="my-quizzes" element={<MyQuizzesPage />} />
        <Route path="my-attempts" element={<MyAttemptsPage />} />
      </Route>
    </Routes>
  );
}
