import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { quizApi } from '@/services/api';
import { quizSchema, emptyQuestion, parseTags, type QuizFormData } from '@/lib/schemas';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Plus, Trash2 } from 'lucide-react';
import type { AnswerOption } from '@/types';

export default function QuizEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: quiz, isLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => quizApi.get(id!),
    enabled: !!id,
  });

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<QuizFormData>({
    resolver: zodResolver(quizSchema),
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'questions',
  });

  useEffect(() => {
    if (quiz) {
      reset({
        title: quiz.title,
        description: quiz.description || '',
        topic: quiz.topic,
        tags: quiz.tags.join(', '),
        questions: quiz.questions.map((q) => ({
          question_text: q.question_text,
          option_a: q.option_a,
          option_b: q.option_b,
          option_c: q.option_c,
          option_d: q.option_d,
          correct_answer: q.correct_answer!,
          explanation: q.explanation || '',
        })),
      });
    }
  }, [quiz, reset]);

  const updateQuiz = useMutation({
    mutationFn: (data: QuizFormData) =>
      quizApi.update(id!, {
        title: data.title,
        description: data.description,
        topic: data.topic,
        tags: parseTags(data.tags),
        questions: data.questions,
      }),
    onSuccess: () => {
      toast({ title: 'Quiz updated successfully!' });
      queryClient.invalidateQueries({ queryKey: ['quiz', id] });
      queryClient.invalidateQueries({ queryKey: ['quizzes'] });
      navigate(`/quizzes/${id}`);
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Failed to update quiz' });
    },
  });

  if (isLoading) {
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Edit Quiz</h1>
        <p className="text-muted-foreground">Update your quiz details and questions</p>
      </div>

      <form onSubmit={handleSubmit((data) => updateQuiz.mutate(data))} className="space-y-6">
        {/* Quiz Details Card */}
        <Card>
          <CardHeader>
            <CardTitle>Quiz Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input id="title" {...register('title')} />
              {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="topic">Topic *</Label>
              <Input id="topic" {...register('topic')} />
              {errors.topic && <p className="text-sm text-destructive">{errors.topic.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" {...register('description')} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input id="tags" {...register('tags')} />
            </div>
          </CardContent>
        </Card>

        {/* Questions Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Questions ({fields.length})</h2>
          <Button type="button" variant="outline" onClick={() => append({ ...emptyQuestion })}>
            <Plus className="mr-2 h-4 w-4" />
            Add Question
          </Button>
        </div>

        {/* Question Cards */}
        {fields.map((field, index) => (
          <Card key={field.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Question {index + 1}</CardTitle>
              {fields.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(index)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Question *</Label>
                <Textarea {...register(`questions.${index}.question_text`)} />
                {errors.questions?.[index]?.question_text && (
                  <p className="text-sm text-destructive">{errors.questions[index]?.question_text?.message}</p>
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {(['a', 'b', 'c', 'd'] as const).map((opt) => (
                  <div key={opt} className="space-y-2">
                    <Label>Option {opt.toUpperCase()} *</Label>
                    <Input {...register(`questions.${index}.option_${opt}`)} />
                    {errors.questions?.[index]?.[`option_${opt}`] && (
                      <p className="text-sm text-destructive">{errors.questions[index]?.[`option_${opt}`]?.message}</p>
                    )}
                  </div>
                ))}
              </div>

              {errors.questions?.[index]?.root && (
                <p className="text-sm text-destructive">{errors.questions[index]?.root?.message}</p>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Correct Answer *</Label>
                  <Select
                    value={watch(`questions.${index}.correct_answer`)}
                    onValueChange={(value) => setValue(`questions.${index}.correct_answer`, value as AnswerOption)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select correct answer" />
                    </SelectTrigger>
                    <SelectContent>
                      {['A', 'B', 'C', 'D'].map((opt) => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Explanation (optional)</Label>
                <Textarea {...register(`questions.${index}.explanation`)} />
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Form-level errors */}
        {errors.questions && !Array.isArray(errors.questions) && (
          <p className="text-sm text-destructive text-center">{errors.questions.message}</p>
        )}
        {errors.questions?.root && (
          <p className="text-sm text-destructive text-center">{errors.questions.root.message}</p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button type="submit" disabled={updateQuiz.isPending}>
            {updateQuiz.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </div>
  );
}
