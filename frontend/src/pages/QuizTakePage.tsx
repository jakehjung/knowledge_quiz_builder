import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { quizApi, attemptApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import type { AnswerOption } from '@/types';

export default function QuizTakePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, AnswerOption | null>>({});
  const initializedRef = useRef(false);

  const { data: quiz, isLoading: quizLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => quizApi.get(id!),
    enabled: !!id,
  });

  // Use a query for starting/resuming attempt since it's idempotent
  const { data: attempt, isLoading: attemptLoading, error: attemptError } = useQuery({
    queryKey: ['attempt', id, 'current'],
    queryFn: () => attemptApi.start(id!),
    enabled: !!id,
    staleTime: 0,
    gcTime: 0, // Don't cache - always get fresh data from server
    retry: 1,
  });

  // Load saved answers ONLY ONCE when attempt data is first available
  useEffect(() => {
    if (attempt?.answers && !initializedRef.current) {
      initializedRef.current = true;
      const initialAnswers: Record<string, AnswerOption | null> = {};
      attempt.answers.forEach((a) => {
        initialAnswers[a.question_id] = a.selected_answer;
      });
      setAnswers(initialAnswers);
    }
  }, [attempt]);

  // Show error toast if attempt failed to start
  useEffect(() => {
    if (attemptError) {
      toast({ variant: 'destructive', title: 'Failed to start quiz' });
    }
  }, [attemptError, toast]);

  const submitAttempt = useMutation({
    mutationFn: (currentAnswers: Record<string, AnswerOption | null>) => {
      const answerList = Object.entries(currentAnswers).map(([question_id, selected_answer]) => ({
        question_id,
        selected_answer,
      }));
      return attemptApi.submit(attempt!.id, answerList);
    },
    onSuccess: (data) => {
      navigate(`/attempts/${data.id}/result`);
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Failed to submit quiz' });
    },
  });


  if (quizLoading || attemptLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading quiz...</p>
        </div>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold">Quiz not found</h2>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;
  const answeredCount = Object.values(answers).filter((a) => a !== null).length;

  const handleAnswerChange = (value: AnswerOption) => {
    const newAnswers = { ...answers, [question.id]: value };
    setAnswers(newAnswers);

    // Save immediately
    if (attempt?.id) {
      const answerList = Object.entries(newAnswers).map(([question_id, selected_answer]) => ({
        question_id,
        selected_answer,
      }));
      attemptApi.saveProgress(attempt.id, answerList);
    }
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleSubmit = () => {
    if (answeredCount < quiz.questions.length) {
      toast({
        variant: 'destructive',
        title: 'Incomplete Quiz',
        description: `Please answer all questions before submitting. You have ${
          quiz.questions.length - answeredCount
        } unanswered.`,
      });
      return;
    }
    submitAttempt.mutate(answers);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{quiz.title}</h1>
        <div className="flex items-center gap-4 mt-2">
          <span className="text-sm text-muted-foreground">
            Question {currentQuestion + 1} of {quiz.questions.length}
          </span>
          <span className="text-sm text-muted-foreground">
            {answeredCount} answered
          </span>
        </div>
        <Progress value={progress} className="mt-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {currentQuestion + 1}. {question.question_text}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            key={question.id}
            value={answers[question.id] || ''}
            onValueChange={(value) => handleAnswerChange(value as AnswerOption)}
          >
            {(['A', 'B', 'C', 'D'] as const).map((option) => {
              const optionKey = `option_${option.toLowerCase()}` as
                | 'option_a'
                | 'option_b'
                | 'option_c'
                | 'option_d';
              return (
                <div key={option} className="flex items-center space-x-2 py-2">
                  <RadioGroupItem value={option} id={`option-${option}`} />
                  <Label htmlFor={`option-${option}`} className="flex-1 cursor-pointer">
                    <span className="font-medium mr-2">{option}.</span>
                    {question[optionKey]}
                  </Label>
                </div>
              );
            })}
          </RadioGroup>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={handlePrevious} disabled={currentQuestion === 0}>
            Previous
          </Button>
          <div className="flex gap-2">
            {currentQuestion < quiz.questions.length - 1 ? (
              <Button onClick={handleNext}>Next</Button>
            ) : (
              <Button onClick={handleSubmit} disabled={submitAttempt.isPending}>
                {submitAttempt.isPending ? 'Submitting...' : 'Submit Quiz'}
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>

      <div className="flex flex-wrap gap-2">
        {quiz.questions.map((q, index) => (
          <Button
            key={q.id}
            variant={
              currentQuestion === index
                ? 'default'
                : answers[q.id]
                ? 'secondary'
                : 'outline'
            }
            size="sm"
            onClick={() => setCurrentQuestion(index)}
          >
            {index + 1}
          </Button>
        ))}
      </div>
    </div>
  );
}
