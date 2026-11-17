"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FolderPlus, Loader2, UserRoundPlus } from "lucide-react";
import { toast } from "sonner";
import { createFolder } from "@/lib/actions/library";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { FolderKind } from "@/lib/types";

type NewFolderDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  parentId: number | null;
  parentName?: string;
  kind?: FolderKind;
};

export function NewFolderDialog({
  open,
  onOpenChange,
  parentId,
  parentName,
  kind = "folder",
}: NewFolderDialogProps) {
  const isAthlete = kind === "athlete";
  const noun = isAthlete ? "athlete" : "folder";
  const router = useRouter();
  const [name, setName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    const trimmed = name.trim();
    if (!trimmed) {
      setError(`Enter ${isAthlete ? "the athlete's" : "a folder"} name`);
      return;
    }

    setPending(true);
    setError(null);
    const result = await createFolder(trimmed, parentId, kind);
    if (result.error) {
      setError(result.error);
      setPending(false);
      return;
    }

    toast.success(isAthlete ? "Athlete added" : "Folder created");
    setPending(false);
    onOpenChange(false);
    router.refresh();
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit} className="space-y-5">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {isAthlete ? (
                <UserRoundPlus className="size-5 text-primary" />
              ) : (
                <FolderPlus className="size-5 text-primary" />
              )}
              New {noun}
            </DialogTitle>
            <DialogDescription>
              {isAthlete
                ? "An athlete is a folder that tracks progress across every photo in it, including subfolders. Its measurements are kept after the 48-hour photo cleanup."
                : parentName
                  ? `Create a subfolder inside “${parentName}”.`
                  : "Create a folder at the top level of your library."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <Label htmlFor="folder-name">
              {isAthlete ? "Athlete name" : "Folder name"}
            </Label>
            <Input
              id="folder-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder={isAthlete ? "e.g. Sam Lee" : "e.g. Block starts"}
              maxLength={120}
              autoFocus
              disabled={pending}
              aria-invalid={Boolean(error)}
            />
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={pending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pending || !name.trim()}>
              {pending ? <Loader2 className="size-4 animate-spin" /> : null}
              {isAthlete ? "Add athlete" : "Create folder"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
