import Link from "next/link";
import {
  ArrowRight,
  Clock3,
  Folder,
  Image as ImageIcon,
  Plus,
  ScanLine,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

export function Dashboard({
  firstName,
  folders,
  images,
  folderCount,
  imageCount,
  latestActivity,
}: DashboardProps) {
  const stats = [
    {
      icon: Folder,
      label: "Folders",
      value: folderCount.toLocaleString(),
      hint: "Organized training sets",
    },
    {
      icon: ScanLine,
      label: "Analyses",
      value: imageCount.toLocaleString(),
      hint: "Sprint frames measured",
    },
    {
      icon: Clock3,
      label: "Latest activity",
      value: latestActivity ? formatRelative(latestActivity) : "—",
      hint: latestActivity ? "Last saved analysis" : "Start your first analysis",
    },
  ];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
      <section className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Dashboard</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">
            Welcome back, {firstName}
          </h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Pick up where you left off or add a fresh sprint frame to your
            library.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button asChild size="lg" className="rounded-full">
            <Link href="/library">
              Open library
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            size="lg"
            className="rounded-full bg-white"
          >
            <Link href="/library?upload=1">
              <Plus className="size-4" />
              Analyze a run
            </Link>
          </Button>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-border/80 shadow-sm">
            <CardContent className="flex items-start gap-3 pt-6">
              <span className="flex size-10 items-center justify-center rounded-xl bg-accent text-primary">
                <stat.icon className="size-5" aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {stat.label}
                </p>
                <p className="mt-1 text-2xl font-semibold tracking-tight">
                  {stat.value}
                </p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {stat.hint}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="mt-10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              Recent folders
            </h2>
            <p className="text-sm text-muted-foreground">
              Jump back into a training set.
            </p>
          </div>
          <Button asChild variant="ghost" size="sm" className="rounded-full">
            <Link href="/library">
              View all
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>

        {folders.length > 0 ? (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {folders.slice(0, 4).map((folder) => (
              <FolderCard
                key={folder.id}
                folder={folder}
                href={`/library?folder=${folder.id}`}
              />
            ))}
          </div>
        ) : (
          <Card className="mt-4 border-dashed border-border bg-white/70">
            <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-accent text-primary">
                <Folder className="size-6" aria-hidden="true" />
              </span>
              <div>
                <p className="font-medium">No folders yet</p>
                <p className="text-sm text-muted-foreground">
                  Create a folder in the library, then upload your first frame.
                </p>
              </div>
              <Button asChild className="rounded-full">
                <Link href="/library?upload=1">
                  <Plus className="size-4" />
                  Add an analysis
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </section>

      <section className="mt-10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              Recent analyses
            </h2>
            <p className="text-sm text-muted-foreground">
              Open a frame to review angles and AI feedback.
            </p>
          </div>
          <Button asChild variant="ghost" size="sm" className="rounded-full">
            <Link href="/library">
              View all
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>

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
          <Card className="mt-4 border-dashed border-border bg-white/70">
            <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-accent text-primary">
                <ImageIcon className="size-6" aria-hidden="true" />
              </span>
              <div>
                <p className="font-medium">No analyses yet</p>
                <p className="text-sm text-muted-foreground">
                  Upload a sprint photo to get pose measurements and feedback.
                </p>
              </div>
              <Button asChild className="rounded-full">
                <Link href="/library?upload=1">
                  <Plus className="size-4" />
                  Upload an image
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </section>

      <Card className="mt-10 overflow-hidden border-border/80 bg-gradient-to-br from-primary to-[#8f1036] text-primary-foreground shadow-lg shadow-primary/15">
        <CardHeader className="sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-white">
              Ready for the next rep?
            </CardTitle>
            <CardDescription className="text-white/80">
              Add a frame and ask the AI coach what to change first.
            </CardDescription>
          </div>
          <Button
            asChild
            variant="secondary"
            size="lg"
            className="mt-3 w-full rounded-full bg-white text-primary hover:bg-white/90 sm:mt-0 sm:w-auto"
          >
            <Link href="/library?upload=1">
              <Plus className="size-4" />
              New analysis
            </Link>
          </Button>
        </CardHeader>
      </Card>
    </main>
  );
}
