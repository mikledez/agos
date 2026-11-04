"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  MessageSquare,
  Loader2,
  RefreshCw,
  Send,
  Trash2,
  UserRound,
} from "lucide-react";
import { toast } from "sonner";
import { CHAT_SUGGESTIONS } from "@/lib/constants";
import { clearChat, sendChatMessage } from "@/lib/actions/library";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

type ChatPanelProps = {
  imageId: number;
  initialMessages: ChatMessage[];
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

function CoachMark() {
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
          {isUser ? <UserRound className="size-4" /> : <CoachMark />}
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

export function ChatPanel({ imageId, initialMessages }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedQuestion, setFailedQuestion] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll the chat only. scrollIntoView would also move the image panel.
    const viewport = bottomRef.current?.closest(
      '[data-slot="scroll-area-viewport"]',
    );
    viewport?.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

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

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="label-caps text-primary">Ask the coach</h3>
          <p className="text-xs text-muted-foreground">
            Follow up about cues, drills, or this phase.
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          onClick={() => {
            void handleClear();
          }}
          disabled={clearing || pending || messages.length === 0}
        >
          {clearing ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Trash2 className="size-3.5" />
          )}
          Clear chat
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-muted/30">
        <ScrollArea className="h-72 px-3 py-3 sm:h-80">
          {messages.length === 0 && !pending ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-2 text-center">
              <span className="flex size-10 items-center justify-center rounded-md bg-accent text-primary">
                <MessageSquare className="size-5" />
              </span>
              <div>
                <p className="text-sm font-medium">Ask about this analysis</p>
                <p className="text-xs text-muted-foreground">
                  The coach only uses the measurements from this photo.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-1.5">
                {CHAT_SUGGESTIONS.map((suggestion) => (
                  <Button
                    key={suggestion}
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-auto bg-card px-3 py-1.5 text-xs font-normal"
                    onClick={() => {
                      void submit(suggestion);
                    }}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {pending ? (
                <div className="flex items-start gap-2.5">
                  <Avatar className="size-8 shrink-0">
                    <AvatarFallback className="bg-accent text-primary">
                      <CoachMark />
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex items-center gap-1 rounded-lg rounded-tl-sm border border-border bg-card px-3.5 py-3">
                    <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.3s]" />
                    <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.15s]" />
                    <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/70" />
                    <span className="sr-only">Coach is typing</span>
                  </div>
                </div>
              ) : null}
              <div ref={bottomRef} />
            </div>
          )}
        </ScrollArea>
      </div>

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
          aria-label="Chat message"
          className="min-h-16 resize-none bg-card"
        />
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] text-muted-foreground">
            AI can make mistakes. Use your judgement.
          </p>
          <div className="flex items-center gap-2">
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
    </section>
  );
}
