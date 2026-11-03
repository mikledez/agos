import { Skeleton } from "@/components/ui/skeleton";

export default function LibraryLoading() {
  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-32 pt-8 sm:px-6 lg:px-8 lg:pt-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-9 w-56" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-28 rounded-full" />
          <Skeleton className="h-9 w-24 rounded-full" />
        </div>
      </div>

      <div className="mt-8 space-y-8">
        <div className="space-y-3">
          <Skeleton className="h-4 w-20" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton
                key={index}
                className="aspect-square w-full rounded-2xl"
              />
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-20" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton
                key={index}
                className="aspect-square w-full rounded-2xl"
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
