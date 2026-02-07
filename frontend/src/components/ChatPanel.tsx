import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chatApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { X, Send, User } from 'lucide-react';
import { Mascot } from './Mascots';
import type { ChatMessage } from '@/types';

interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
  theme: 'byu' | 'utah';
}

export default function ChatPanel({ open, onClose, theme }: ChatPanelProps) {
  const assistantName = theme === 'byu' ? 'Cosmo the Cougar' : 'Swoop the Ute';
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      return chatApi.send(message, history);
    },
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);
      setTimeout(() => inputRef.current?.focus(), 0);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ]);
      setTimeout(() => inputRef.current?.focus(), 0);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sendMessage.isPending) return;

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    sendMessage.mutate(userMessage);
  };

  if (!open) return null;

  return (
    <div className="fixed bottom-0 right-0 top-0 z-50 flex w-full flex-col border-l bg-background shadow-lg sm:w-96">
      <div className="flex items-center justify-between border-b p-4 bg-primary text-primary-foreground">
        <div className="flex items-center space-x-2">
          <div className="bg-white rounded-full p-1">
            <Mascot theme={theme} className="h-8 w-8" />
          </div>
          <h2 className="font-semibold">{assistantName}</h2>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="text-primary-foreground hover:bg-primary-foreground/20">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground">
            <Mascot theme={theme} className="mx-auto h-16 w-16 mb-4" />
            <p className="text-sm">
              Hi! I'm {assistantName}. I can help you create and manage quizzes. Try asking me to:
            </p>
            <ul className="mt-2 text-sm space-y-1">
              <li>Create a quiz about a topic</li>
              <li>List your quizzes</li>
              <li>Show quiz analytics</li>
              <li>Edit or delete a quiz</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex max-w-[80%] items-start space-x-2 ${
                message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  message.role === 'user' ? 'bg-primary' : 'bg-muted'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="h-4 w-4 text-primary-foreground" />
                ) : (
                  <Mascot theme={theme} className="h-6 w-6" />
                )}
              </div>
              <div
                className={`rounded-lg px-3 py-2 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          </div>
        ))}

        {sendMessage.isPending && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                <Mascot theme={theme} className="h-6 w-6" />
              </div>
              <div className="rounded-lg bg-muted px-3 py-2">
                <div className="flex space-x-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about quizzes..."
            disabled={sendMessage.isPending}
          />
          <Button type="submit" size="icon" disabled={sendMessage.isPending || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
