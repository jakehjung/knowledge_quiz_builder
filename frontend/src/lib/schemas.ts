import { z } from 'zod';
import type { AnswerOption } from '@/types';

/**
 * Question validation schema with duplicate option checking.
 */
export const questionSchema = z
  .object({
    question_text: z.string().min(1, 'Question is required'),
    option_a: z.string().min(1, 'Option A is required'),
    option_b: z.string().min(1, 'Option B is required'),
    option_c: z.string().min(1, 'Option C is required'),
    option_d: z.string().min(1, 'Option D is required'),
    correct_answer: z.enum(['A', 'B', 'C', 'D']),
    explanation: z.string().optional(),
  })
  .refine(
    (data) => {
      const options = [
        data.option_a.trim().toLowerCase(),
        data.option_b.trim().toLowerCase(),
        data.option_c.trim().toLowerCase(),
        data.option_d.trim().toLowerCase(),
      ];
      return new Set(options).size === options.length;
    },
    { message: 'All answer options must be unique (no duplicates allowed)' }
  );

/**
 * Quiz validation schema for create/edit forms.
 */
export const quizSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().max(1000).optional(),
  topic: z.string().min(1, 'Topic is required').max(255),
  tags: z.string().optional(),
  questions: z.array(questionSchema).min(1, 'Quiz must have at least 1 question'),
});

export type QuizFormData = z.infer<typeof quizSchema>;

/**
 * Empty question template for adding new questions.
 */
export const emptyQuestion: QuizFormData['questions'][0] = {
  question_text: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  correct_answer: 'A' as AnswerOption,
  explanation: '',
};

/**
 * Parse comma-separated tags string into array.
 */
export function parseTags(tagsString?: string): string[] {
  if (!tagsString) return [];
  return tagsString.split(',').map((t) => t.trim()).filter(Boolean);
}
