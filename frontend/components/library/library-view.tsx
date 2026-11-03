"use client";

import { Fragment, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  FolderPlus,
  ImagePlus,
  Library,
  Plus,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DeleteDialog } from "@/components/library/delete-dialog";
import { FolderCard } from "@/components/library/folder-card";
import { ImageCard } from "@/components/library/image-card";
import { ImageSheet } from "@/components/library/image-sheet";
import { NewFolderDialog } from "@/components/library/new-folder-dialog";
import { RenameDialog } from "@/components/library/rename-dialog";
import { UploadDialog } from "@/components/library/upload-dialog";
import { backendAssetUrl } from "@/lib/backend";
import type {
  ChatMessage,
  Folder,
  ImageDetail,
  SprintImage,
} from "@/lib/types";

type RenameTarget =
  | { kind: "folder"; id: number; name: string }
  | { kind: "image"; id: number; name: string };

type DeleteTarget =
  | { kind: "folder"; id: number; name: string }
  | { kind: "image"; id: number; name: string };

type LibraryViewProps = {
  folder: Folder | null;
  breadcrumb: Folder[];
  folders: Folder[];
  images: SprintImage[];
  imageDetail: ImageDetail | null;
  messages: ChatMessage[];
  autoOpenUpload: boolean;
};

export function LibraryView({
  folder,
  breadcrumb,
  folders,
  images,
  imageDetail,
  messages,
  autoOpenUpload,
}: LibraryViewProps) {
  const router = useRouter();
  const [newFolderOpen, setNewFolderOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(autoOpenUpload);
  const [renameTarget, setRenameTarget] = useState<RenameTarget | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);

  useEffect(() => {
    if (!autoOpenUpload) return;
    const url = new URL(window.location.href);
    url.searchParams.delete("upload");
    window.history.replaceState({}, "", url.toString());
  }, [autoOpenUpload]);

  const basePath = folder ? `/library?folder=${folder.id}` : "/library";
  const imageHref = (image: SprintImage) =>
    folder
      ? `${basePath}&image=${image.id}`
      : `/library?image=${image.id}`;

  function closeImage() {
    router.push(basePath, { scroll: false });
  }

  function handleDeleted(target: DeleteTarget) {
    if (target.kind === "image" && imageDetail?.image.id === target.id) {
      router.push(basePath, { scroll: false });
    }
    if (target.kind === "folder" && folder?.id === target.id) {
      router.push(
        folder.parent_id ? `/library?folder=${folder.parent_id}` : "/library",
      );
    }
  }

  const isEmpty = folders.length === 0 && images.length === 0;

  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-32 pt-8 sm:px-6 lg:px-8 lg:pt-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                {folder ? (
                  <BreadcrumbLink asChild>
                    <Link href="/library">Library</Link>
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage>Library</BreadcrumbPage>
                )}
              </BreadcrumbItem>
              {breadcrumb.map((item, index) => {
                const isLast =
                  index === breadcrumb.length - 1 && folder?.id === item.id;
                return (
                  <Fragment key={item.id}>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      {isLast ? (
                        <BreadcrumbPage>{item.name}</BreadcrumbPage>
                      ) : (
                        <BreadcrumbLink asChild>
                          <Link href={`/library?folder=${item.id}`}>
                            {item.name}
                          </Link>
                        </BreadcrumbLink>
                      )}
                    </BreadcrumbItem>
                  </Fragment>
                );
              })}
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="mt-3 truncate text-3xl font-semibold tracking-tight sm:text-4xl">
            {folder?.name ?? "Library"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {isEmpty
              ? "Nothing here yet."
              : `${folders.length} folder${folders.length === 1 ? "" : "s"} · ${images.length} image${images.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            type="button"
            variant="outline"
            className="rounded-full bg-white"
            onClick={() => setNewFolderOpen(true)}
          >
            <FolderPlus className="size-4" />
            New folder
          </Button>
          <Button
            type="button"
            className="rounded-full"
            onClick={() => setUploadOpen(true)}
          >
            <UploadCloud className="size-4" />
            Upload
          </Button>
        </div>
      </div>

      {isEmpty ? (
        <section className="mt-10">
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-border bg-white/70 px-6 py-16 text-center">
            <span className="flex size-14 items-center justify-center rounded-2xl bg-accent text-primary">
              {folder ? (
                <Library className="size-7" aria-hidden="true" />
              ) : (
                <FolderPlus className="size-7" aria-hidden="true" />
              )}
            </span>
            <h2 className="mt-4 text-xl font-semibold">
              {folder ? "This folder is empty" : "Your library is empty"}
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {folder
                ? "Add a sprint frame or create a subfolder to keep this training set organized."
                : "Upload a sprint photo to get pose measurements, AI feedback, and a persistent coach chat."}
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row">
              <Button
                type="button"
                className="rounded-full"
                onClick={() => setUploadOpen(true)}
              >
                <ImagePlus className="size-4" />
                Upload an image
              </Button>
              <Button
                type="button"
                variant="outline"
                className="rounded-full bg-white"
                onClick={() => setNewFolderOpen(true)}
              >
                <FolderPlus className="size-4" />
                New folder
              </Button>
            </div>
          </div>
        </section>
      ) : (
        <div className="mt-8 space-y-8">
          {folders.length > 0 ? (
            <section>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Folders
                </h2>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {folders.map((item) => (
                  <FolderCard
                    key={item.id}
                    folder={item}
                    href={`/library?folder=${item.id}`}
                    onRename={(target) =>
                      setRenameTarget({
                        kind: "folder",
                        id: target.id,
                        name: target.name,
                      })
                    }
                    onDelete={(target) =>
                      setDeleteTarget({
                        kind: "folder",
                        id: target.id,
                        name: target.name,
                      })
                    }
                  />
                ))}
              </div>
            </section>
          ) : null}

          {images.length > 0 ? (
            <section>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Images
                </h2>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {images.map((image) => (
                  <ImageCard
                    key={image.id}
                    image={image}
                    href={imageHref(image)}
                    src={backendAssetUrl(
                      image.annotated_url ?? image.original_url,
                    )}
                    onRename={(target) =>
                      setRenameTarget({
                        kind: "image",
                        id: target.id,
                        name: target.original_filename,
                      })
                    }
                    onDelete={(target) =>
                      setDeleteTarget({
                        kind: "image",
                        id: target.id,
                        name: target.original_filename,
                      })
                    }
                  />
                ))}
              </div>
            </section>
          ) : null}
        </div>
      )}

      <div className="fixed bottom-6 right-4 z-30 sm:right-6">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              size="icon-lg"
              className="size-14 rounded-full shadow-lg shadow-primary/30 transition hover:scale-105 hover:shadow-xl"
              aria-label="Add to library"
            >
              <Plus className="size-6" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="end" className="w-48">
            <DropdownMenuItem onSelect={() => setNewFolderOpen(true)}>
              <FolderPlus className="size-4" />
              New folder
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => setUploadOpen(true)}>
              <UploadCloud className="size-4" />
              Upload image
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <NewFolderDialog
        key={newFolderOpen ? "folder-open" : "folder-closed"}
        open={newFolderOpen}
        onOpenChange={setNewFolderOpen}
        parentId={folder?.id ?? null}
        parentName={folder?.name}
      />

      <UploadDialog
        key={uploadOpen ? "upload-open" : "upload-closed"}
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        folderId={folder?.id ?? null}
        folderName={folder?.name}
      />

      <RenameDialog
        key={
          renameTarget
            ? `rename-${renameTarget.kind}-${renameTarget.id}`
            : "rename-closed"
        }
        target={renameTarget}
        onOpenChange={(open) => {
          if (!open) setRenameTarget(null);
        }}
      />

      <DeleteDialog
        key={
          deleteTarget
            ? `delete-${deleteTarget.kind}-${deleteTarget.id}`
            : "delete-closed"
        }
        target={deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        onDeleted={handleDeleted}
      />

      {imageDetail ? (
        <ImageSheet
          key={imageDetail.image.id}
          detail={imageDetail}
          messages={messages}
          onClose={closeImage}
          onRename={(image) =>
            setRenameTarget({
              kind: "image",
              id: image.id,
              name: image.original_filename,
            })
          }
          onDelete={(image) =>
            setDeleteTarget({
              kind: "image",
              id: image.id,
              name: image.original_filename,
            })
          }
        />
      ) : null}

      <div className="mt-12 flex items-center justify-center gap-1 text-xs text-muted-foreground">
        <ArrowRight className="size-3" aria-hidden="true" />
        Use the breadcrumb to move up a folder level.
      </div>
    </main>
  );
}
