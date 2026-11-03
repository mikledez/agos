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
    <div className="group relative overflow-hidden rounded-2xl border border-border/80 bg-card shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-md">
      <Link href={href} className="flex aspect-square flex-col">
        <div className="flex flex-1 items-center justify-center bg-gradient-to-br from-accent via-secondary/70 to-card">
          <span className="flex size-16 items-center justify-center rounded-2xl bg-white/75 text-primary shadow-sm ring-1 ring-primary/10 transition group-hover:scale-105">
            <Folder className="size-8" aria-hidden="true" />
          </span>
        </div>
        <div className="p-3">
          <p className="truncate text-sm font-semibold">{folder.name}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Updated {formatDate(folder.updated_at)}
          </p>
        </div>
      </Link>

      {hasMenu ? (
        <div className="absolute right-2 top-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="secondary"
                size="icon-sm"
                className="rounded-full bg-white/85 shadow-sm backdrop-blur hover:bg-white"
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
