import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/store/AuthContext';
import { useTheme } from '@/store/ThemeContext';
import { quizApi, attemptApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BookOpen, Plus, BarChart3, Users, TrendingUp } from 'lucide-react';
import { Mascot } from '@/components/Mascots';

export default function HomePage() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const isInstructor = user?.role === 'instructor';

  const { data: recentQuizzes } = useQuery({
    queryKey: ['quizzes', 'recent'],
    queryFn: () => quizApi.list({ page_size: 5, sort: 'newest' }),
  });

  const { data: myAttempts } = useQuery({
    queryKey: ['attempts', 'my'],
    queryFn: () => attemptApi.getMyAttempts(),
    enabled: !isInstructor, // Only for students
  });

  const { data: myQuizzes } = useQuery({
    queryKey: ['quizzes', 'my'],
    queryFn: () => quizApi.getMyQuizzes(),
    enabled: isInstructor,
  });

  const { data: instructorStats } = useQuery({
    queryKey: ['quizzes', 'my', 'stats'],
    queryFn: () => quizApi.getMyStats(),
    enabled: isInstructor,
  });

  // Student stats
  const completedAttempts = myAttempts?.attempts.filter((a) => a.status === 'completed') || [];
  const bestScores = completedAttempts.reduce(
    (acc, attempt) => {
      if (!acc[attempt.quiz_id] || (attempt.score || 0) > acc[attempt.quiz_id].score) {
        acc[attempt.quiz_id] = {
          score: attempt.score || 0,
          total_questions: attempt.total_questions,
        };
      }
      return acc;
    },
    {} as Record<string, { score: number; total_questions: number }>
  );
  const totalBestScore = Object.values(bestScores).reduce((a, b) => a + b.score, 0);
  const totalPossible = Object.values(bestScores).reduce((a, b) => a + b.total_questions, 0);

  return (
    <div className="space-y-8">
      {/* Welcome Header with Mascot */}
      <div className="flex items-center gap-6">
        <Mascot theme={theme} className="h-20 w-20 hidden sm:block" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.display_name || user?.email}!
          </h1>
          <p className="text-muted-foreground">
            {isInstructor
              ? 'Manage your quizzes or create new ones with AI assistance.'
              : 'Discover quizzes and test your knowledge.'}
          </p>
        </div>
      </div>

      {/* INSTRUCTOR VIEW */}
      {isInstructor ? (
        <>
          {/* Instructor Stats */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">My Quizzes</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{myQuizzes?.total || 0}</div>
                <p className="text-xs text-muted-foreground">quizzes created</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Students</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{instructorStats?.total_students ?? 0}</div>
                <p className="text-xs text-muted-foreground">across all quizzes</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Score</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {instructorStats?.average_percentage !== undefined
                    ? `${instructorStats.average_percentage.toFixed(0)}%`
                    : '0%'}
                </div>
                <p className="text-xs text-muted-foreground">student performance</p>
              </CardContent>
            </Card>

            <Card className="bg-primary text-primary-foreground">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-primary-foreground">Quick Actions</CardTitle>
                <Plus className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Button asChild size="sm" variant="secondary" className="w-full">
                  <Link to="/quizzes/create">Create New Quiz</Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Instructor Main Content */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* My Quizzes */}
            <Card>
              <CardHeader>
                <CardTitle>My Quizzes</CardTitle>
                <CardDescription>Quizzes you've created</CardDescription>
              </CardHeader>
              <CardContent>
                {!myQuizzes?.quizzes || myQuizzes.quizzes.length === 0 ? (
                  <div className="text-center py-6">
                    <Mascot theme={theme} className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-muted-foreground text-sm mb-4">
                      You haven't created any quizzes yet.
                    </p>
                    <Button asChild>
                      <Link to="/quizzes/create">Create Your First Quiz</Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myQuizzes.quizzes.slice(0, 5).map((quiz) => (
                      <div key={quiz.id} className="flex items-center justify-between">
                        <div>
                          <Link
                            to={`/quizzes/${quiz.id}`}
                            className="font-medium hover:underline"
                          >
                            {quiz.title}
                          </Link>
                          <p className="text-sm text-muted-foreground">{quiz.topic}</p>
                        </div>
                        <Button asChild size="sm" variant="outline">
                          <Link to={`/quizzes/${quiz.id}/analytics`}>
                            <BarChart3 className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                {myQuizzes?.quizzes && myQuizzes.quizzes.length > 0 && (
                  <div className="mt-4">
                    <Button asChild variant="outline" className="w-full">
                      <Link to="/my-quizzes">View All My Quizzes</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Browse All Quizzes */}
            <Card>
              <CardHeader>
                <CardTitle>Browse Quizzes</CardTitle>
                <CardDescription>Recent quizzes from all instructors</CardDescription>
              </CardHeader>
              <CardContent>
                {recentQuizzes?.quizzes.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No quizzes available yet.</p>
                ) : (
                  <div className="space-y-4">
                    {recentQuizzes?.quizzes.map((quiz) => (
                      <div key={quiz.id} className="flex items-center justify-between">
                        <div>
                          <Link
                            to={`/quizzes/${quiz.id}`}
                            className="font-medium hover:underline"
                          >
                            {quiz.title}
                          </Link>
                          <p className="text-sm text-muted-foreground">
                            by {quiz.instructor.display_name || quiz.instructor.email}
                          </p>
                        </div>
                        <Button asChild size="sm" variant="outline">
                          <Link to={`/quizzes/${quiz.id}`}>View</Link>
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-4">
                  <Button asChild variant="outline" className="w-full">
                    <Link to="/quizzes">Browse All Quizzes</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        /* STUDENT VIEW */
        <>
          {/* Student Stats */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Quizzes Taken</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(bestScores).length}</div>
                <p className="text-xs text-muted-foreground">unique quizzes completed</p>
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
                  {totalPossible > 0 ? Math.round((totalBestScore / totalPossible) * 100) : 0}%
                </div>
                <p className="text-xs text-muted-foreground">overall performance</p>
              </CardContent>
            </Card>

            <Card className="bg-primary text-primary-foreground">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-primary-foreground">Ready to Learn?</CardTitle>
                <BookOpen className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Button asChild size="sm" variant="secondary" className="w-full">
                  <Link to="/quizzes">Find a Quiz</Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Student Main Content */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Recent Quizzes */}
            <Card>
              <CardHeader>
                <CardTitle>Discover Quizzes</CardTitle>
                <CardDescription>Newest quizzes available to take</CardDescription>
              </CardHeader>
              <CardContent>
                {recentQuizzes?.quizzes.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No quizzes available yet.</p>
                ) : (
                  <div className="space-y-4">
                    {recentQuizzes?.quizzes.map((quiz) => (
                      <div key={quiz.id} className="flex items-center justify-between">
                        <div>
                          <Link
                            to={`/quizzes/${quiz.id}`}
                            className="font-medium hover:underline"
                          >
                            {quiz.title}
                          </Link>
                          <p className="text-sm text-muted-foreground">{quiz.topic}</p>
                        </div>
                        <Button asChild size="sm">
                          <Link to={`/quizzes/${quiz.id}`}>Take Quiz</Link>
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-4">
                  <Button asChild variant="outline" className="w-full">
                    <Link to="/quizzes">Browse All Quizzes</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Your Progress</CardTitle>
                <CardDescription>Your recent quiz attempts</CardDescription>
              </CardHeader>
              <CardContent>
                {myAttempts?.attempts.length === 0 ? (
                  <div className="text-center py-6">
                    <Mascot theme={theme} className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-muted-foreground text-sm mb-4">
                      You haven't taken any quizzes yet. Start learning!
                    </p>
                    <Button asChild>
                      <Link to="/quizzes">Find a Quiz</Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myAttempts?.attempts.slice(0, 5).map((attempt) => (
                      <div key={attempt.id} className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{attempt.quiz_title}</p>
                          <p className="text-sm text-muted-foreground">
                            {attempt.status === 'completed'
                              ? `Score: ${attempt.score}/${attempt.total_questions}`
                              : 'In progress'}
                          </p>
                        </div>
                        {attempt.status === 'completed' ? (
                          <Button asChild size="sm" variant="outline">
                            <Link to={`/attempts/${attempt.id}/result`}>Results</Link>
                          </Button>
                        ) : (
                          <Button asChild size="sm">
                            <Link to={`/quizzes/${attempt.quiz_id}/take`}>Continue</Link>
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {myAttempts?.attempts && myAttempts.attempts.length > 0 && (
                  <div className="mt-4">
                    <Button asChild variant="outline" className="w-full">
                      <Link to="/my-attempts">View All Attempts</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
