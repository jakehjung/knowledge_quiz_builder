import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/store/AuthContext';
import { quizApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BookOpen, Clock, User, Edit, BarChart3, Trash2, CheckCircle2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { useMutation, useQueryClient } from '@tanstack/react-query';

export default function QuizDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: quiz, isLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => quizApi.get(id!),
    enabled: !!id,
  });

  const deleteQuiz = useMutation({
    mutationFn: () => quizApi.delete(id!),
    onSuccess: () => {
      toast({ title: 'Quiz deleted successfully' });
      queryClient.invalidateQueries({ queryKey: ['quizzes'] });
      navigate('/my-quizzes');
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Failed to delete quiz' });
    },
  });

  const isOwner = user?.id === quiz?.instructor.id;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-muted rounded w-1/3 animate-pulse" />
        <div className="h-4 bg-muted rounded w-1/2 animate-pulse" />
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-muted rounded w-1/4" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-muted rounded" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="text-center py-12">
        <BookOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold">Quiz not found</h2>
        <p className="text-muted-foreground">The quiz you're looking for doesn't exist.</p>
        <Button asChild className="mt-4">
          <Link to="/quizzes">Browse Quizzes</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{quiz.title}</h1>
          <p className="text-muted-foreground mt-1">{quiz.topic}</p>
        </div>
        <div className="flex gap-2">
          {isOwner && (
            <>
              <Button asChild variant="outline">
                <Link to={`/quizzes/${id}/edit`}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link to={`/quizzes/${id}/analytics`}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Analytics
                </Link>
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Quiz?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. This will permanently delete the quiz and all
                      associated data.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => deleteQuiz.mutate()}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </>
          )}
          <Button asChild>
            <Link to={`/quizzes/${id}/take`}>Take Quiz</Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>About this Quiz</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>{quiz.description || 'No description provided.'}</p>

            {quiz.tags.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {quiz.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quiz Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <span>{quiz.questions.length} questions</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span>By {quiz.instructor.display_name || quiz.instructor.email}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span>No time limit</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Questions Preview</CardTitle>
          <CardDescription>
            {isOwner
              ? "Review your quiz questions. Correct answers are highlighted in green."
              : "A preview of what you'll be answering"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {quiz.questions.map((question, index) => {
              const options = [
                { letter: 'A', text: question.option_a },
                { letter: 'B', text: question.option_b },
                { letter: 'C', text: question.option_c },
                { letter: 'D', text: question.option_d },
              ];

              return (
                <div key={question.id} className="border-b pb-4 last:border-0 last:pb-0">
                  <p className="font-medium">
                    {index + 1}. {question.question_text}
                  </p>
                  <div className="mt-2 grid gap-1 text-sm">
                    {options.map(({ letter, text }) => {
                      const isCorrect = isOwner && question.correct_answer === letter;
                      return (
                        <span
                          key={letter}
                          className={
                            isCorrect
                              ? "text-green-600 font-medium flex items-center gap-1"
                              : "text-muted-foreground"
                          }
                        >
                          {isCorrect && <CheckCircle2 className="h-4 w-4" />}
                          {letter}. {text}
                        </span>
                      );
                    })}
                  </div>
                  {isOwner && question.explanation && (
                    <p className="mt-2 text-sm text-muted-foreground bg-muted p-2 rounded">
                      <strong>Explanation:</strong> {question.explanation}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
