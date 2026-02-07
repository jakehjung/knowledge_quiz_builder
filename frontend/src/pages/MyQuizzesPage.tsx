import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { quizApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Edit, BarChart3, BookOpen } from 'lucide-react';

export default function MyQuizzesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['quizzes', 'my'],
    queryFn: () => quizApi.getMyQuizzes(),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Quizzes</h1>
          <p className="text-muted-foreground">Manage your created quizzes</p>
        </div>
        <Button asChild>
          <Link to="/quizzes/create">
            <Plus className="mr-2 h-4 w-4" />
            Create Quiz
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-1/2 mt-2" />
              </CardHeader>
              <CardContent>
                <div className="h-4 bg-muted rounded w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : data?.quizzes.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <BookOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No quizzes yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first quiz to get started
            </p>
            <Button asChild>
              <Link to="/quizzes/create">
                <Plus className="mr-2 h-4 w-4" />
                Create Quiz
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.quizzes.map((quiz) => (
            <Card key={quiz.id}>
              <CardHeader>
                <CardTitle className="line-clamp-1">{quiz.title}</CardTitle>
                <CardDescription className="line-clamp-1">{quiz.topic}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {quiz.description || 'No description provided'}
                </p>
                {quiz.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {quiz.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-full bg-muted px-2 py-1 text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  {quiz.is_published ? 'Published' : 'Draft'} •{' '}
                  {new Date(quiz.created_at).toLocaleDateString()}
                </p>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button asChild size="sm" variant="outline">
                  <Link to={`/quizzes/${quiz.id}/edit`}>
                    <Edit className="mr-1 h-3 w-3" />
                    Edit
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to={`/quizzes/${quiz.id}/analytics`}>
                    <BarChart3 className="mr-1 h-3 w-3" />
                    Analytics
                  </Link>
                </Button>
                <Button asChild size="sm">
                  <Link to={`/quizzes/${quiz.id}`}>View</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
