"use client";

import { Fragment, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FolderPlus,
  ImagePlus,
  Library,
  Plus,
  UploadCloud,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
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
    <div className="mx-auto max-w-screen-2xl px-4 pb-32 pt-8 sm:px-6 lg:px-8 lg:pt-10">
      <PageHeader
        eyebrow={
          folder ? (
            <div className="normal-case tracking-normal">
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
            </div>
          ) : undefined
        }
        title={folder?.name ?? "Library"}
        description={
          isEmpty
            ? "Nothing here yet."
            : `${folders.length} folder${folders.length === 1 ? "" : "s"} · ${images.length} image${images.length === 1 ? "" : "s"}`
        }
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              onClick={() => setNewFolderOpen(true)}
            >
              <FolderPlus className="size-4" />
              New folder
            </Button>
            <Button type="button" onClick={() => setUploadOpen(true)}>
              <UploadCloud className="size-4" />
              Upload
            </Button>
          </>
        }
      />

      {isEmpty ? (
        <EmptyState
          icon={folder ? Library : FolderPlus}
          title={folder ? "This folder is empty" : "Your library is empty"}
          description={
            folder
              ? "Add a sprint frame or create a subfolder to keep this training set organized."
              : "Upload a sprint photo to get pose measurements, AI feedback, and a chat for each frame."
          }
          className="mt-8 py-16"
          action={
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button type="button" onClick={() => setUploadOpen(true)}>
                <ImagePlus className="size-4" />
                Upload an image
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setNewFolderOpen(true)}
              >
                <FolderPlus className="size-4" />
                New folder
              </Button>
            </div>
          }
        />
      ) : (
        <div className="mt-8 space-y-8">
          {folders.length > 0 ? (
            <section>
              <h2 className="label-caps mb-3 text-muted-foreground">Folders</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
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
              <h2 className="label-caps mb-3 text-muted-foreground">Images</h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
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
              className="size-14 rounded-lg shadow-md"
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
          backLabel={folder?.name ?? "Library"}
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
    </div>
  );
}
