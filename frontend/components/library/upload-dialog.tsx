"use client";

/* eslint-disable @next/next/no-img-element */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ImagePlus,
  Loader2,
  RefreshCw,
  UploadCloud,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { DIRECTIONS, PHASES } from "@/lib/constants";
import { prepareImage } from "@/lib/image";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type UploadDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  folderId: number | null;
  folderName?: string;
};

type AnalyzeResponse = {
  image_id: number;
  detail?: string;
  error?: string;
};

const MAX_FILE_BYTES = 10 * 1024 * 1024;

export function UploadDialog({
  open,
  onOpenChange,
  folderId,
  folderName,
}: UploadDialogProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [phase, setPhase] = useState<string>("toe_off");
  const [direction, setDirection] = useState<string>("ltr");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!preview) return;
    return () => URL.revokeObjectURL(preview);
  }, [preview]);

  function selectFile(next: File | undefined) {
    if (!next) return;
    if (!next.type.startsWith("image/") && !/\.(heic|heif)$/i.test(next.name)) {
      setError("Choose a JPEG, PNG, WebP, or HEIC image.");
      return;
    }
    if (next.size > MAX_FILE_BYTES) {
      setError("Images must be 10 MB or smaller.");
      return;
    }
    setError(null);
    setFile(next);
    setPreview(URL.createObjectURL(next));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (uploading) return;
    if (!file) {
      setError("Choose an image first.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const upload = await prepareImage(file);
      const body = new FormData();
      body.append("file", upload, upload.name);
      body.append("phase", phase);
      body.append("direction", direction);
      if (folderId !== null) body.append("session_id", String(folderId));

      const response = await fetch("/api/backend/analyze", {
        method: "POST",
        body,
      });

      let data: AnalyzeResponse | null = null;
      try {
        data = (await response.json()) as AnalyzeResponse;
      } catch {
        data = null;
      }

      if (!response.ok) {
        setError(
          data?.detail || data?.error || `Request failed (${response.status})`,
        );
        setUploading(false);
        return;
      }
      if (!data?.image_id) {
        setError("The server returned an unexpected response.");
        setUploading(false);
        return;
      }

      toast.success("Analysis complete");
      setUploading(false);
      setFile(null);
      setPreview(null);
      onOpenChange(false);
      router.refresh();
      router.push(
        `/library${folderId !== null ? `?folder=${folderId}&` : "?"}image=${data.image_id}`,
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not upload this image.",
      );
      setUploading(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => !uploading && onOpenChange(next)}
    >
      <DialogContent className="sm:max-w-lg">
        <form ref={formRef} onSubmit={handleSubmit} className="space-y-5">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ImagePlus className="size-5 text-primary" />
              Upload image
            </DialogTitle>
            <DialogDescription>
              {folderName
                ? `Analyze a sprint frame and save it in “${folderName}”.`
                : "Analyze a sprint frame and save it at the top level of your library."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <Label htmlFor="image-file">Sprint photo</Label>
            <input
              ref={inputRef}
              id="image-file"
              type="file"
              accept="image/*,.heic,.heif"
              className="sr-only"
              onChange={(event) => selectFile(event.target.files?.[0])}
              disabled={uploading}
            />

            {preview ? (
              <div className="relative overflow-hidden rounded-xl border bg-muted">
                <img
                  src={preview}
                  alt="Selected sprint frame preview"
                  className="max-h-64 w-full object-contain"
                />
                {!uploading ? (
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="secondary"
                    className="absolute right-2 top-2 rounded-full bg-white/90"
                    onClick={() => {
                      setFile(null);
                      setPreview(null);
                    }}
                    aria-label="Remove selected image"
                  >
                    <X className="size-4" />
                  </Button>
                ) : null}
                {uploading ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/75 backdrop-blur-sm">
                    <Loader2 className="size-6 animate-spin text-primary" />
                    <p className="text-sm font-medium">Analyzing pose…</p>
                    <Skeleton className="h-2 w-40" />
                  </div>
                ) : null}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  selectFile(event.dataTransfer.files?.[0]);
                }}
                disabled={uploading}
                className={cn(
                  "flex w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed px-4 py-10 text-center transition-colors",
                  dragging
                    ? "border-primary bg-accent"
                    : "border-border bg-muted/40 hover:border-primary/40 hover:bg-accent/60",
                )}
              >
                <span className="flex size-11 items-center justify-center rounded-full bg-white text-primary shadow-sm">
                  <UploadCloud className="size-5" />
                </span>
                <span className="text-sm font-medium">
                  Drop an image here or click to browse
                </span>
                <span className="text-xs text-muted-foreground">
                  JPEG, PNG, WebP, or HEIC. Large photos are resized
                  automatically.
                </span>
              </button>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="upload-phase">Phase</Label>
              <Select
                value={phase}
                onValueChange={setPhase}
                disabled={uploading}
              >
                <SelectTrigger id="upload-phase" className="w-full">
                  <SelectValue placeholder="Select phase" />
                </SelectTrigger>
                <SelectContent>
                  {PHASES.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="upload-direction">Direction</Label>
              <Select
                value={direction}
                onValueChange={setDirection}
                disabled={uploading}
              >
                <SelectTrigger id="upload-direction" className="w-full">
                  <SelectValue placeholder="Select direction" />
                </SelectTrigger>
                <SelectContent>
                  {DIRECTIONS.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {error ? (
            <Alert variant="destructive">
              <AlertCircle className="size-4" />
              <AlertTitle>Upload failed</AlertTitle>
              <AlertDescription>
                <p>{error}</p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2 bg-white"
                  onClick={() => formRef.current?.requestSubmit()}
                  disabled={uploading || !file}
                >
                  <RefreshCw className="size-3.5" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          ) : null}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={uploading || !file}
              className="min-w-32"
            >
              {uploading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Analyzing…
                </>
              ) : (
                "Analyze image"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
