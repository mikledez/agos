import Link from "next/link";
import {
  ArrowRight,
  Folder,
  Image as ImageIcon,
  Plus,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { FolderCard } from "@/components/library/folder-card";
import { ImageCard } from "@/components/library/image-card";
import { backendAssetUrl } from "@/lib/backend";
import { formatRelative } from "@/lib/format";
import type { Folder as FolderType, SprintImage } from "@/lib/types";

type DashboardProps = {
  firstName: string;
  folders: FolderType[];
  images: SprintImage[];
  folderCount: number;
  imageCount: number;
  latestActivity: string | null;
};

function SectionHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div>
        <h2 className="display-type text-3xl">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      <Button asChild variant="ghost" size="sm">
        <Link href="/library">
          View all
          <ArrowRight className="size-4" />
        </Link>
      </Button>
    </div>
  );
}

export function Dashboard({
  firstName,
  folders,
  images,
  folderCount,
  imageCount,
  latestActivity,
}: DashboardProps) {
  return (
    <div className="mx-auto max-w-screen-2xl space-y-10 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome back, ${firstName}`}
        description="Pick up where you left off or add a fresh sprint frame to your library."
        actions={
          <>
            <Button asChild variant="outline">
              <Link href="/library">Open library</Link>
            </Button>
            <Button asChild>
              <Link href="/library?upload=1">
                <Plus className="size-4" />
                Analyze a run
              </Link>
            </Button>
          </>
        }
      />

      <dl className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Folders"
          value={folderCount.toLocaleString()}
          hint="Organized training sets"
        />
        <StatCard
          label="Analyses"
          value={imageCount.toLocaleString()}
          hint="Sprint frames measured"
        />
        <StatCard
          label="Latest activity"
          value={latestActivity ? formatRelative(latestActivity) : "—"}
          hint={latestActivity ? "Last saved analysis" : "Start your first analysis"}
        />
      </dl>

      <section>
        <SectionHeading
          title="Recent folders"
          description="Jump back into a training set."
        />
        {folders.length > 0 ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {folders.slice(0, 4).map((folder) => (
              <FolderCard
                key={folder.id}
                folder={folder}
                href={`/library?folder=${folder.id}`}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Folder}
            title="No folders yet"
            description="Create a folder in the library, then upload your first frame."
            className="mt-4"
            action={
              <Button asChild>
                <Link href="/library?upload=1">
                  <Plus className="size-4" />
                  Add an analysis
                </Link>
              </Button>
            }
          />
        )}
      </section>

      <section>
        <SectionHeading
          title="Recent analyses"
          description="Open a frame to review angles and feedback."
        />
        {images.length > 0 ? (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {images.slice(0, 4).map((image) => (
              <ImageCard
                key={image.id}
                image={image}
                href={`/library${
                  image.session_id ? `?folder=${image.session_id}&` : "?"
                }image=${image.id}`}
                src={backendAssetUrl(
                  image.annotated_url ?? image.original_url,
                )}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ImageIcon}
            title="No analyses yet"
            description="Upload a sprint photo to get pose measurements and feedback."
            className="mt-4"
            action={
              <Button asChild>
                <Link href="/library?upload=1">
                  <Plus className="size-4" />
                  Upload an image
                </Link>
              </Button>
            }
          />
        )}
      </section>
    </div>
  );
}
