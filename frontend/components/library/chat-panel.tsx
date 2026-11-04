"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Loader2,
  RefreshCw,
  Send,
  Trash2,
  UserRound,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { CHAT_SUGGESTIONS } from "@/lib/constants";
import {
  clearChat,
  generateFeedback,
  sendChatMessage,
} from "@/lib/actions/library";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { ChatMessage, Humanization } from "@/lib/types";

type ChatPanelProps = {
  imageId: number;
  initialMessages: ChatMessage[];
  initialFeedback: Humanization | null;
};

const MAX_CHARS = 1000;

function optimisticMessage(imageId: number, content: string): ChatMessage {
  return {
    id: -Date.now(),
    image_id: imageId,
    role: "user",
    content,
    model: null,
    created_at: new Date().toISOString(),
  };
}

function AiMark() {
  return (
    <span aria-hidden="true" className="font-display text-base font-extrabold italic">
      Ā
    </span>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex items-start gap-2.5",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      <Avatar className="size-8 shrink-0">
        <AvatarFallback
          className={cn(
            "text-[10px] font-semibold",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-accent text-primary",
          )}
        >
          {isUser ? <UserRound className="size-4" /> : <AiMark />}
        </AvatarFallback>
      </Avatar>
      <div
        className={cn(
          "max-w-[82%] whitespace-pre-wrap rounded-lg px-3.5 py-2.5 text-sm leading-6",
          isUser
            ? "rounded-tr-sm bg-primary text-primary-foreground"
            : "rounded-tl-sm border border-border bg-card text-card-foreground",
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

export function ChatPanel({
  imageId,
  initialMessages,
  initialFeedback,
}: ChatPanelProps) {
  const router = useRouter();
  const [feedback, setFeedback] = useState<Humanization | null>(initialFeedback);
  const [generating, setGenerating] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedQuestion, setFailedQuestion] = useState<string | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const thread = threadRef.current;
    thread?.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  async function handleGenerate() {
    if (generating) return;
    setGenerating(true);
    setFeedbackError(null);
    const result = await generateFeedback(imageId);
    if (result.error || !result.humanization) {
      setFeedbackError(result.error ?? "Could not generate AI feedback");
      toast.error(result.error ?? "Could not generate AI feedback");
      setGenerating(false);
      return;
    }
    setFeedback(result.humanization);
    setGenerating(false);
    toast.success("AI feedback ready");
    router.refresh();
  }

  async function submit(content: string) {
    const text = content.trim();
    if (!text || pending) return;

    setInput("");
    setError(null);
    setFailedQuestion(null);
    const optimistic = optimisticMessage(imageId, text);
    setMessages((previous) => [...previous, optimistic]);
    setPending(true);

    const result = await sendChatMessage(imageId, text);

    if (result.error || !result.exchange) {
      setError(result.error ?? "Could not get an answer");
      setFailedQuestion(text);
      setPending(false);
      return;
    }

    setMessages((previous) => [
      ...previous.filter((message) => message.id !== optimistic.id),
      result.exchange!.user_message,
      result.exchange!.assistant_message,
    ]);
    setPending(false);
  }

  function retry() {
    if (!failedQuestion) return;
    const question = failedQuestion;
    setMessages((previous) =>
      previous.filter(
        (message) =>
          !(
            message.id < 0 &&
            message.role === "user" &&
            message.content === question
          ),
      ),
    );
    setError(null);
    setFailedQuestion(null);
    void submit(question);
  }

  async function handleClear() {
    if (clearing || pending) return;
    setClearing(true);
    const result = await clearChat(imageId);
    if (result.error) {
      toast.error(result.error);
    } else {
      setMessages([]);
      setError(null);
      setFailedQuestion(null);
      toast.success("Chat cleared");
    }
    setClearing(false);
  }

  const hasThread = messages.length > 0 || pending;

  return (
    <section className="rounded-lg border border-primary/20 bg-card">
      <div className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="label-caps text-primary">AI feedback</h3>
            {feedback ? (
              <p className="mt-1 text-[11px] text-muted-foreground">
                Model: {feedback.model}
              </p>
            ) : null}
          </div>
          <Button
            type="button"
            size="sm"
            variant={feedback ? "outline" : "default"}
            onClick={() => {
              void handleGenerate();
            }}
            disabled={generating}
            className="shrink-0"
          >
            {generating ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : feedback ? (
              <RefreshCw className="size-3.5" />
            ) : null}
            {feedback ? "Regenerate" : "Generate AI feedback"}
          </Button>
        </div>

        {feedbackError ? (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertTitle>Could not generate AI feedback</AlertTitle>
            <AlertDescription>{feedbackError}</AlertDescription>
          </Alert>
        ) : null}

        {feedback ? (
          <p className="whitespace-pre-wrap text-sm leading-6">
            {feedback.humanized_text}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            No AI feedback yet. Generate a short summary from these
            measurements.
          </p>
        )}
      </div>

      <div className="space-y-3 border-t border-border p-5">
        <div className="flex min-h-8 items-center justify-between gap-3">
          <h3 className="label-caps text-primary">Ask AI</h3>
          {messages.length > 0 ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={() => {
                void handleClear();
              }}
              disabled={clearing || pending}
            >
              {clearing ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Trash2 className="size-3.5" />
              )}
              Clear chat
            </Button>
          ) : null}
        </div>

        {hasThread ? (
          <div
            ref={threadRef}
            className="max-h-80 space-y-3 overflow-y-auto rounded-lg border border-border bg-muted/30 p-3"
          >
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {pending ? (
              <div className="flex items-start gap-2.5">
                <Avatar className="size-8 shrink-0">
                  <AvatarFallback className="bg-accent text-primary">
                    <AiMark />
                  </AvatarFallback>
                </Avatar>
                <div className="flex items-center gap-1 rounded-lg rounded-tl-sm border border-border bg-card px-3.5 py-3">
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.3s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.15s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70" />
                  <span className="sr-only">AI is typing</span>
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {CHAT_SUGGESTIONS.map((suggestion) => (
              <Button
                key={suggestion}
                type="button"
                variant="outline"
                size="sm"
                className="h-auto px-3 py-1.5 text-xs font-normal"
                onClick={() => {
                  void submit(suggestion);
                }}
              >
                {suggestion}
              </Button>
            ))}
          </div>
        )}

        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertTitle>Could not get an answer</AlertTitle>
            <AlertDescription>
              <p>{error}</p>
              {failedQuestion ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={retry}
                  disabled={pending}
                >
                  <RefreshCw className="size-3.5" />
                  Retry
                </Button>
              ) : null}
            </AlertDescription>
          </Alert>
        ) : null}

        <div className="space-y-1.5">
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value.slice(0, MAX_CHARS))}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit(input);
              }
            }}
            placeholder="Ask about drills, cues, or your angles…"
            rows={2}
            maxLength={MAX_CHARS}
            disabled={pending || clearing}
            aria-label="Ask AI"
            className="min-h-16 resize-none bg-card"
          />
          <div className="flex items-center justify-between gap-2">
            <p className="text-[11px] text-muted-foreground">
              AI only uses the measurements from this photo and can make
              mistakes.
            </p>
            <div className="flex shrink-0 items-center gap-2">
              <span
                className={cn(
                  "text-[11px] tabular-nums",
                  input.length >= MAX_CHARS
                    ? "text-destructive"
                    : "text-muted-foreground",
                )}
              >
                {input.length}/{MAX_CHARS}
              </span>
              <Button
                type="button"
                size="icon"
                onClick={() => {
                  void submit(input);
                }}
                disabled={pending || clearing || !input.trim()}
                aria-label="Send message"
              >
                {pending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Send className="size-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
