"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { ExternalLink, MoreVertical, Pencil, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DIRECTION_LABEL, PHASE_LABEL } from "@/lib/constants";
import { formatDate } from "@/lib/format";
import type { SprintImage } from "@/lib/types";

type ImageCardProps = {
  image: SprintImage;
  href: string;
  src: string | null;
  onRename?: (image: SprintImage) => void;
  onDelete?: (image: SprintImage) => void;
};

export function ImageCard({
  image,
  href,
  src,
  onRename,
  onDelete,
}: ImageCardProps) {
  const hasMenu = Boolean(onRename || onDelete);

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border/80 bg-card shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-md">
      <Link href={href} className="block">
        <div className="relative aspect-square overflow-hidden bg-muted">
          {src ? (
            <img
              src={src}
              alt={image.original_filename}
              className="size-full object-cover transition duration-300 group-hover:scale-[1.02]"
              loading="lazy"
            />
          ) : (
            <div className="flex size-full items-center justify-center text-xs text-muted-foreground">
              No preview
            </div>
          )}
          <div className="absolute inset-x-2 bottom-2 flex flex-wrap gap-1">
            <Badge className="border-0 bg-black/65 text-white backdrop-blur">
              {PHASE_LABEL[image.phase] ?? image.phase}
            </Badge>
            <Badge
              variant="secondary"
              className="border-0 bg-white/85 text-foreground backdrop-blur"
            >
              {DIRECTION_LABEL[image.direction] ?? image.direction}
            </Badge>
          </div>
        </div>
        <div className="p-3">
          <p className="truncate text-sm font-semibold">
            {image.original_filename}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {formatDate(image.created_at)}
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
                aria-label={`Actions for ${image.original_filename}`}
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem asChild>
                <Link href={href}>
                  <ExternalLink className="size-4" />
                  Open
                </Link>
              </DropdownMenuItem>
              {onRename ? (
                <DropdownMenuItem onSelect={() => onRename(image)}>
                  <Pencil className="size-4" />
                  Rename
                </DropdownMenuItem>
              ) : null}
              {onDelete ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    variant="destructive"
                    onSelect={() => onDelete(image)}
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
