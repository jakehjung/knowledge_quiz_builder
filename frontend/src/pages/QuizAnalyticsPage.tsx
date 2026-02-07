import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { quizApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Users, Trophy, BarChart3, Target, ArrowLeft } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function QuizAnalyticsPage() {
  const { id } = useParams<{ id: string }>();

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['quiz', id, 'analytics'],
    queryFn: () => quizApi.getAnalytics(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold">Analytics not available</h2>
      </div>
    );
  }

  const totalQuestions = analytics.total_questions;
  const scoreDistributionData = Object.entries(analytics.score_distribution || {}).map(
    ([score, count]) => ({
      score: `${score}/${totalQuestions}`,
      count,
    })
  );

  const questionAccuracyData = (analytics.question_analysis || []).map((q, idx) => ({
    name: `Q${idx + 1}`,
    accuracy: q.accuracy_rate,
    question: q.question_text,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="sm">
          <Link to={`/quizzes/${id}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Quiz
          </Link>
        </Button>
      </div>

      <div>
        <h1 className="text-3xl font-bold tracking-tight">{analytics.quiz_title}</h1>
        <p className="text-muted-foreground">Quiz Analytics and Performance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Attempts</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_attempts}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.unique_students}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.average_score.toFixed(1)}/{totalQuestions}</div>
            <p className="text-xs text-muted-foreground">
              {((analytics.average_score / totalQuestions) * 100).toFixed(0)}% accuracy
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics.total_attempts > 0
                ? (
                    (Object.entries(analytics.score_distribution || {})
                      .filter(([score]) => Number(score) / totalQuestions >= 0.6)
                      .reduce((sum, [, count]) => sum + count, 0) /
                      analytics.total_attempts) *
                    100
                  ).toFixed(0)
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground">Score 60% or higher</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>How students scored on this quiz</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.total_attempts === 0 ? (
              <p className="text-muted-foreground text-center py-8">No data available yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={scoreDistributionData}>
                  <XAxis dataKey="score" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Question Difficulty</CardTitle>
            <CardDescription>Accuracy rate per question</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.total_attempts === 0 ? (
              <p className="text-muted-foreground text-center py-8">No data available yet</p>
            ) : (
              <div className="space-y-4">
                {questionAccuracyData.map((q, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="truncate max-w-[200px]" title={q.question}>
                        {q.name}: {q.question.substring(0, 30)}...
                      </span>
                      <span>{q.accuracy.toFixed(0)}%</span>
                    </div>
                    <Progress value={q.accuracy} className="h-2" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Student Leaderboard</CardTitle>
          <CardDescription>Top performers on this quiz</CardDescription>
        </CardHeader>
        <CardContent>
          {(analytics.student_scores || []).length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No students have taken this quiz yet
            </p>
          ) : (
            <div className="space-y-4">
              {analytics.student_scores.slice(0, 10).map((student, idx) => (
                <div key={student.user_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-muted-foreground w-8">
                      {idx + 1}
                    </span>
                    <div>
                      <p className="font-medium">{student.display_name || student.email}</p>
                      <p className="text-sm text-muted-foreground">
                        {student.attempts_count} attempt{student.attempts_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">{student.best_score}/{totalQuestions}</p>
                    <p className="text-sm text-muted-foreground">Best Score</p>
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
