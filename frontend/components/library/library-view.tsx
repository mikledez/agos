"use client";

import { Fragment, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FolderPlus,
  Library,
  Plus,
  UploadCloud,
  UserRoundPlus,
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
import { toast } from "sonner";
import { AthleteProgressPanel } from "@/components/library/athlete-progress";
import { setFolderKind } from "@/lib/actions/library";
import type {
  AthleteProgress,
  ChatMessage,
  Folder,
  FolderKind,
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
  progress: AthleteProgress | null;
  autoOpenUpload: boolean;
};

export function LibraryView({
  folder,
  breadcrumb,
  folders,
  images,
  imageDetail,
  messages,
  progress,
  autoOpenUpload,
}: LibraryViewProps) {
  const router = useRouter();
  const [newFolderOpen, setNewFolderOpen] = useState(false);
  const [newFolderKind, setNewFolderKind] = useState<FolderKind>("folder");
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

  function openNewFolder(kind: FolderKind) {
    setNewFolderKind(kind);
    setNewFolderOpen(true);
  }

  async function toggleKind(target: Folder) {
    const kind: FolderKind = target.kind === "athlete" ? "folder" : "athlete";
    const result = await setFolderKind(target.id, kind);
    if (result.error) {
      toast.error(result.error);
      return;
    }
    toast.success(
      kind === "athlete"
        ? `${target.name} now tracks progress`
        : `${target.name} is a regular folder again`,
    );
    router.refresh();
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
      />

      {folder?.kind === "athlete" && progress ? (
        <AthleteProgressPanel progress={progress} className="mt-8" />
      ) : null}

      {isEmpty ? (
        <EmptyState
          icon={folder ? Library : FolderPlus}
          title={folder ? "This folder is empty" : "Your library is empty"}
          description={
            folder
              ? "Use the + button to add a sprint frame or a subfolder."
              : "Use the + button to upload a sprint photo or create a folder."
          }
          className="mt-8 py-16"
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
                    onToggleKind={toggleKind}
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
                    src={backendAssetUrl(image.thumbnail_url)}
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
            <DropdownMenuItem onSelect={() => openNewFolder("folder")}>
              <FolderPlus className="size-4" />
              New folder
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => openNewFolder("athlete")}>
              <UserRoundPlus className="size-4" />
              New athlete
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
        kind={newFolderKind}
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
