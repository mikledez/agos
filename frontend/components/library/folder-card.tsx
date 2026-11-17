"use client";

import Link from "next/link";
import {
  Folder,
  FolderInput,
  MoreVertical,
  Pencil,
  Trash2,
  UserRound,
} from "lucide-react";
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
  onToggleKind?: (folder: FolderType) => void;
  onDelete?: (folder: FolderType) => void;
};

export function FolderCard({
  folder,
  href,
  onRename,
  onToggleKind,
  onDelete,
}: FolderCardProps) {
  const hasMenu = Boolean(onRename || onToggleKind || onDelete);
  const isAthlete = folder.kind === "athlete";
  const Icon = isAthlete ? UserRound : Folder;

  return (
    <div className="group relative rounded-lg border border-border bg-card transition-colors hover:border-primary/30">
      <Link
        href={href}
        className="flex items-center gap-3 rounded-lg p-4 pr-12 outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-accent text-primary">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold group-hover:text-primary">
            {folder.name}
          </span>
          <span className="mt-0.5 block truncate text-xs text-muted-foreground">
            {isAthlete ? "Athlete · " : "Updated "}
            {formatDate(folder.updated_at)}
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
                className="size-10 text-muted-foreground sm:size-8"
                aria-label={`Actions for ${folder.name}`}
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {onRename ? (
                <DropdownMenuItem onSelect={() => onRename(folder)}>
                  <Pencil className="size-4" />
                  Rename
                </DropdownMenuItem>
              ) : null}
              {onToggleKind ? (
                <DropdownMenuItem onSelect={() => onToggleKind(folder)}>
                  {isAthlete ? (
                    <FolderInput className="size-4" />
                  ) : (
                    <UserRound className="size-4" />
                  )}
                  {isAthlete ? "Make a regular folder" : "Make an athlete"}
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
