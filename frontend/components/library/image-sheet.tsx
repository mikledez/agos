"use client";

/* eslint-disable @next/next/no-img-element */

import { useState } from "react";
import {
  AlertCircle,
  Loader2,
  MoreVertical,
  Pencil,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { generateFeedback } from "@/lib/actions/library";
import { DIRECTION_LABEL, PHASE_LABEL } from "@/lib/constants";
import { angle } from "@/lib/format";
import { backendAssetUrl } from "@/lib/backend";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChatPanel } from "@/components/library/chat-panel";
import type {
  ChatMessage,
  Humanization,
  ImageDetail,
  SprintImage,
} from "@/lib/types";

type ImageSheetProps = {
  detail: ImageDetail;
  messages: ChatMessage[];
  onClose: () => void;
  onRename: (image: SprintImage) => void;
  onDelete: (image: SprintImage) => void;
};

type LegMetrics = {
  title: string;
  hip: number | null;
  knee: number | null;
  ankle: number | null;
  feedback: string | null;
};

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background px-2.5 py-2">
      <p className="label-caps text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-display text-2xl font-bold leading-none tabular-nums">{value}</p>
    </div>
  );
}

function LegCard({ metrics }: { metrics: LegMetrics }) {
  return (
    <Card className="gap-3 py-5">
      <CardHeader className="px-5">
        <CardTitle className="label-caps text-muted-foreground">{metrics.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 px-5">
        <div className="grid grid-cols-3 gap-2">
          <MetricTile label="Hip" value={angle(metrics.hip)} />
          <MetricTile label="Knee" value={angle(metrics.knee)} />
          <MetricTile label="Ankle" value={angle(metrics.ankle)} />
        </div>
        <p className="text-sm leading-6 text-muted-foreground">
          {metrics.feedback || "No feedback for this leg."}
        </p>
      </CardContent>
    </Card>
  );
}

export function ImageSheet({
  detail,
  messages,
  onClose,
  onRename,
  onDelete,
}: ImageSheetProps) {
  const router = useRouter();
  const { image } = detail;
  const [feedback, setFeedback] = useState<Humanization | null>(
    detail.humanization,
  );
  const [generating, setGenerating] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [view, setView] = useState<"annotated" | "original">(
    image.annotated_url ? "annotated" : "original",
  );

  const src =
    backendAssetUrl(
      view === "annotated"
        ? image.annotated_url ?? image.original_url
        : image.original_url,
    ) ?? "";

  async function handleGenerate() {
    if (generating) return;
    setGenerating(true);
    setFeedbackError(null);
    const result = await generateFeedback(image.id);
    if (result.error || !result.humanization) {
      setFeedbackError(result.error ?? "Could not generate feedback");
      toast.error(result.error ?? "Could not generate feedback");
      setGenerating(false);
      return;
    }
    setFeedback(result.humanization);
    setGenerating(false);
    toast.success("Feedback ready");
    router.refresh();
  }

  return (
    <Sheet open onOpenChange={(next) => !next && onClose()}>
      <SheetContent
        side="right"
        className="w-full overflow-y-auto p-0 sm:max-w-[720px]"
      >
        <SheetHeader className="sticky top-0 z-10 gap-2 border-b border-border bg-background/95 p-5 pr-14 backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <SheetTitle className="display-type truncate pb-0.5 text-2xl">
                {image.original_filename}
              </SheetTitle>
              <SheetDescription className="mt-1 flex flex-wrap items-center gap-1.5">
                <Badge variant="secondary">
                  {PHASE_LABEL[image.phase] ?? image.phase}
                </Badge>
                <Badge variant="outline">
                  {DIRECTION_LABEL[image.direction] ?? image.direction}
                </Badge>
              </SheetDescription>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="mr-6 shrink-0"
                  aria-label="Image actions"
                >
                  <MoreVertical className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onSelect={() => onRename(image)}>
                  <Pencil className="size-4" />
                  Rename
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant="destructive"
                  onSelect={() => onDelete(image)}
                >
                  <Trash2 className="size-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </SheetHeader>

        <div className="space-y-6 p-5">
          <section className="space-y-3">
            <Tabs
              value={view}
              onValueChange={(value) => setView(value as "annotated" | "original")}
            >
              <TabsList className="grid w-full grid-cols-2 sm:w-auto">
                <TabsTrigger value="annotated" disabled={!image.annotated_url}>
                  Annotated
                </TabsTrigger>
                <TabsTrigger value="original">Original</TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="overflow-hidden rounded-lg border border-border bg-muted/40">
              <img
                src={src}
                alt={image.original_filename}
                className="max-h-[440px] w-full object-contain"
              />
            </div>
          </section>

          <section className="grid gap-3 sm:grid-cols-2">
            <LegCard
              metrics={{
                title: "Swing leg",
                hip: image.swing_hip,
                knee: image.swing_knee,
                ankle: image.swing_ankle,
                feedback: image.swing_feedback,
              }}
            />
            <LegCard
              metrics={{
                title: "Stance leg",
                hip: image.stance_hip,
                knee: image.stance_knee,
                ankle: image.stance_ankle,
                feedback: image.stance_feedback,
              }}
            />
          </section>

          <Card className="gap-3 py-5">
            <CardHeader className="px-5">
              <CardTitle className="label-caps text-muted-foreground">Overall</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 px-5 text-sm leading-6 text-muted-foreground">
              {image.thigh_thigh != null ? (
                <p>
                  <span className="font-medium text-foreground">
                    Thigh separation:
                  </span>{" "}
                  {angle(image.thigh_thigh)}
                </p>
              ) : null}
              <p>{image.feedback || "No overall feedback for this frame."}</p>
            </CardContent>
          </Card>

          <Card className="gap-3 border-primary/20 py-5">
            <CardHeader className="flex flex-row items-start justify-between gap-3 px-5">
              <div>
                <CardTitle className="label-caps text-primary">
                  Coach feedback
                </CardTitle>
                {feedback ? (
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Model: {feedback.model}
                  </p>
                ) : null}
              </div>
              <Button
                type="button"
                size="sm"
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
                {feedback ? "Regenerate" : "Generate feedback"}
              </Button>
            </CardHeader>
            <CardContent className="space-y-3 px-5">
              {feedbackError ? (
                <Alert variant="destructive">
                  <AlertCircle className="size-4" />
                  <AlertTitle>Could not generate feedback</AlertTitle>
                  <AlertDescription>{feedbackError}</AlertDescription>
                </Alert>
              ) : null}
              {feedback ? (
                <p className="text-sm leading-6">{feedback.humanized_text}</p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No feedback yet. Generate a concise coaching summary from
                  these measurements.
                </p>
              )}
            </CardContent>
          </Card>

          <ChatPanel
            key={image.id}
            imageId={image.id}
            initialMessages={messages}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
