"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Pencil } from "lucide-react";
import { toast } from "sonner";
import { renameFolder, renameImage } from "@/lib/actions/library";
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

type RenameTarget =
  | { kind: "folder"; id: number; name: string }
  | { kind: "image"; id: number; name: string };

type RenameDialogProps = {
  target: RenameTarget | null;
  onOpenChange: (open: boolean) => void;
};

export function RenameDialog({ target, onOpenChange }: RenameDialogProps) {
  const router = useRouter();
  const [name, setName] = useState(target?.name ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!target || pending) return;

    const trimmed = name.trim();
    if (!trimmed) {
      setError("Enter a name");
      return;
    }

    setPending(true);
    setError(null);
    const result =
      target.kind === "folder"
        ? await renameFolder(target.id, trimmed)
        : await renameImage(target.id, trimmed);

    if (result.error) {
      setError(result.error);
      setPending(false);
      return;
    }

    toast.success(target.kind === "folder" ? "Folder renamed" : "Image renamed");
    setPending(false);
    onOpenChange(false);
    router.refresh();
  }

  return (
    <Dialog
      open={Boolean(target)}
      onOpenChange={(next) => !pending && onOpenChange(next)}
    >
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit} className="space-y-5">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pencil className="size-5 text-primary" />
              Rename {target?.kind === "folder" ? "folder" : "image"}
            </DialogTitle>
            <DialogDescription>
              Choose a clear name so it is easy to find later.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <Label htmlFor="rename-name">Name</Label>
            <Input
              id="rename-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={200}
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
              Save name
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
