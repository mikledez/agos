"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { deleteFolder, deleteImage } from "@/lib/actions/library";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

type DeleteTarget =
  | { kind: "folder"; id: number; name: string }
  | { kind: "image"; id: number; name: string };

type DeleteDialogProps = {
  target: DeleteTarget | null;
  onOpenChange: (open: boolean) => void;
  onDeleted?: (target: DeleteTarget) => void;
};

export function DeleteDialog({
  target,
  onOpenChange,
  onDeleted,
}: DeleteDialogProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (!target || pending) return;
    setPending(true);
    setError(null);

    const result =
      target.kind === "folder"
        ? await deleteFolder(target.id)
        : await deleteImage(target.id);

    if (result.error) {
      setError(result.error);
      setPending(false);
      return;
    }

    toast.success(target.kind === "folder" ? "Folder deleted" : "Image deleted");
    setPending(false);
    onOpenChange(false);
    onDeleted?.(target);
    router.refresh();
  }

  return (
    <AlertDialog
      open={Boolean(target)}
      onOpenChange={(next) => !pending && onOpenChange(next)}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Trash2 className="size-5 text-destructive" />
            Delete {target?.kind === "folder" ? "folder" : "image"}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            {target?.kind === "folder" ? (
              <>
                “{target.name}” and all nested folders and images inside it will
                be permanently deleted. This cannot be undone.
              </>
            ) : (
              <>
                “{target?.name}” will be permanently deleted, including its AI
                feedback and chat history. This cannot be undone.
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Cancel</AlertDialogCancel>
          <Button
            type="button"
            variant="destructive"
            onClick={() => {
              void handleDelete();
            }}
            disabled={pending}
          >
            {pending ? <Loader2 className="size-4 animate-spin" /> : null}
            Delete
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
