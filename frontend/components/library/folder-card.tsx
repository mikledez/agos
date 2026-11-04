"use client";

import Link from "next/link";
import { Folder, MoreVertical, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatDate } from "@/lib/format";
import type { Folder as FolderType } from "@/lib/types";

type FolderCardProps = {
  folder: FolderType;
  href: string;
  onRename?: (folder: FolderType) => void;
  onDelete?: (folder: FolderType) => void;
};

export function FolderCard({
  folder,
  href,
  onRename,
  onDelete,
}: FolderCardProps) {
  const hasMenu = Boolean(onRename || onDelete);

  return (
    <div className="group relative rounded-lg border border-border bg-card transition-colors hover:border-primary/30">
      <Link
        href={href}
        className="flex items-center gap-3 rounded-lg p-4 pr-12 outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-accent text-primary">
          <Folder className="size-5" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold group-hover:text-primary">
            {folder.name}
          </span>
          <span className="mt-0.5 block truncate text-xs text-muted-foreground">
            Updated {formatDate(folder.updated_at)}
          </span>
        </span>
      </Link>

      {hasMenu ? (
        <div className="absolute right-2 top-1/2 -translate-y-1/2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground"
                aria-label={`Actions for ${folder.name}`}
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {onRename ? (
                <DropdownMenuItem onSelect={() => onRename(folder)}>
                  <Pencil className="size-4" />
                  Rename
                </DropdownMenuItem>
              ) : null}
              {onDelete ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    variant="destructive"
                    onSelect={() => onDelete(folder)}
                  >
                    <Trash2 className="size-4" />
                    Delete
                  </DropdownMenuItem>
                </>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ) : null}
    </div>
  );
}
