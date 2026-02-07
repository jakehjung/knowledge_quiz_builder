import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { attemptApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, XCircle, Trophy, RotateCcw } from 'lucide-react';

export default function QuizResultPage() {
  const { attemptId } = useParams<{ attemptId: string }>();

  const { data: result, isLoading } = useQuery({
    queryKey: ['attempt', attemptId],
    queryFn: () => attemptApi.get(attemptId!),
    enabled: !!attemptId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold">Results not found</h2>
      </div>
    );
  }

  const percentage = ((result.score || 0) / result.total_questions) * 100;
  const isPassing = percentage >= 60;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card className="text-center">
        <CardContent className="pt-6">
          <div
            className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${
              isPassing ? 'bg-green-100' : 'bg-red-100'
            } mb-4`}
          >
            <Trophy className={`h-10 w-10 ${isPassing ? 'text-green-600' : 'text-red-600'}`} />
          </div>
          <h1 className="text-3xl font-bold mb-2">
            {result.score}/{result.total_questions}
          </h1>
          <p className="text-xl text-muted-foreground mb-4">{percentage.toFixed(0)}% Correct</p>
          <h2 className="text-lg font-medium">{result.quiz_title}</h2>

          <div className="flex justify-center gap-4 mt-6">
            <Button asChild variant="outline">
              <Link to={`/quizzes/${result.quiz_id}`}>View Quiz</Link>
            </Button>
            <Button asChild>
              <Link to={`/quizzes/${result.quiz_id}/take`}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Retake Quiz
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Review Your Answers</h2>

        {result.questions.map((question, index) => (
          <Card
            key={question.id}
            className={question.is_correct ? 'border-green-200' : 'border-red-200'}
          >
            <CardHeader className="pb-2">
              <div className="flex items-start gap-2">
                {question.is_correct ? (
                  <CheckCircle className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                )}
                <CardTitle className="text-base">
                  {index + 1}. {question.question_text}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {(['A', 'B', 'C', 'D'] as const).map((option) => {
                  const optionKey = `option_${option.toLowerCase()}` as
                    | 'option_a'
                    | 'option_b'
                    | 'option_c'
                    | 'option_d';
                  const isCorrect = question.correct_answer === option;
                  const isSelected = question.selected_answer === option;

                  return (
                    <div
                      key={option}
                      className={`p-2 rounded ${
                        isCorrect
                          ? 'bg-green-50 border border-green-200'
                          : isSelected && !isCorrect
                          ? 'bg-red-50 border border-red-200'
                          : ''
                      }`}
                    >
                      <span className="font-medium mr-2">{option}.</span>
                      {question[optionKey]}
                      {isCorrect && (
                        <span className="ml-2 text-green-600 text-xs">(Correct Answer)</span>
                      )}
                      {isSelected && !isCorrect && (
                        <span className="ml-2 text-red-600 text-xs">(Your Answer)</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {question.explanation && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-1">Explanation:</p>
                  <p className="text-sm text-muted-foreground">{question.explanation}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-center gap-4">
        <Button asChild variant="outline">
          <Link to="/quizzes">Browse More Quizzes</Link>
        </Button>
        <Button asChild>
          <Link to="/my-attempts">View All Attempts</Link>
        </Button>
      </div>
    </div>
  );
}
