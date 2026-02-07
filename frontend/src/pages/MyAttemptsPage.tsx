import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { attemptApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, BookOpen, CheckCircle, Clock, TrendingUp } from 'lucide-react';

export default function MyAttemptsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['attempts', 'my'],
    queryFn: () => attemptApi.getMyAttempts(),
  });

  const completedAttempts = data?.attempts.filter((a) => a.status === 'completed') || [];
  const inProgressAttempts = data?.attempts.filter((a) => a.status === 'in_progress') || [];

  // Calculate best scores per quiz
  const bestScores = completedAttempts.reduce(
    (acc, attempt) => {
      if (!acc[attempt.quiz_id] || (attempt.score || 0) > acc[attempt.quiz_id].score) {
        acc[attempt.quiz_id] = {
          score: attempt.score || 0,
          quiz_title: attempt.quiz_title,
          total_questions: attempt.total_questions,
        };
      }
      return acc;
    },
    {} as Record<string, { score: number; quiz_title: string; total_questions: number }>
  );

  const totalBestScore = Object.values(bestScores).reduce((a, b) => a + b.score, 0);
  const totalPossible = Object.values(bestScores).reduce((a, b) => a + b.total_questions, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Attempts</h1>
        <p className="text-muted-foreground">Track your quiz history and progress</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quizzes Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(bestScores).length}</div>
            <p className="text-xs text-muted-foreground">unique quizzes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Attempts</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedAttempts.length}</div>
            <p className="text-xs text-muted-foreground">quiz attempts made</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalPossible > 0 ? ((totalBestScore / totalPossible) * 100).toFixed(0) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">overall performance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inProgressAttempts.length}</div>
            <p className="text-xs text-muted-foreground">incomplete quizzes</p>
          </CardContent>
        </Card>
      </div>

      {inProgressAttempts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Continue Where You Left Off</CardTitle>
            <CardDescription>Resume your incomplete quizzes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {inProgressAttempts.map((attempt) => (
                <div key={attempt.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{attempt.quiz_title}</p>
                    <p className="text-sm text-muted-foreground">
                      Started {new Date(attempt.started_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button asChild size="sm">
                    <Link to={`/quizzes/${attempt.quiz_id}/take`}>Continue</Link>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Completed Quizzes</CardTitle>
          <CardDescription>Your quiz history and scores</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-muted rounded animate-pulse" />
              ))}
            </div>
          ) : completedAttempts.length === 0 ? (
            <div className="text-center py-8">
              <BookOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No completed quizzes yet</h3>
              <p className="text-muted-foreground mb-4">Take a quiz to see your results here</p>
              <Button asChild>
                <Link to="/quizzes">Browse Quizzes</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {completedAttempts.map((attempt) => (
                <div
                  key={attempt.id}
                  className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
                >
                  <div>
                    <Link
                      to={`/quizzes/${attempt.quiz_id}`}
                      className="font-medium hover:underline"
                    >
                      {attempt.quiz_title}
                    </Link>
                    <p className="text-sm text-muted-foreground">
                      {new Date(attempt.completed_at || attempt.started_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-bold">
                        {attempt.score}/{attempt.total_questions}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {((attempt.score || 0) / attempt.total_questions * 100).toFixed(0)}%
                      </p>
                    </div>
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/attempts/${attempt.id}/result`}>View Results</Link>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
