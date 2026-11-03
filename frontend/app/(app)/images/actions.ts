"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { backendFetch } from "@/lib/backend";

function imageIdFrom(formData: FormData): string {
  return String(formData.get("image_id") ?? "");
}

export async function generateHumanization(formData: FormData): Promise<void> {
  const imageId = imageIdFrom(formData);
  if (!imageId) return;

  const response = await backendFetch(
    `/images/${imageId}/humanization/generate`,
    { method: "POST" },
  );

  if (!response.ok) {
    let detail = "Could not generate feedback";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      const text = await response.text().catch(() => "");
      if (text) detail = text;
    }
    redirect(`/images/${imageId}?error=${encodeURIComponent(detail)}`);
  }

  revalidatePath(`/images/${imageId}`);
  redirect(`/images/${imageId}`);
}

export async function deleteImage(formData: FormData): Promise<void> {
  const imageId = imageIdFrom(formData);
  if (!imageId) return;

  const response = await backendFetch(`/images/${imageId}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    throw new Error(await response.text());
  }
  revalidatePath("/sessions");
  redirect("/sessions");
}
