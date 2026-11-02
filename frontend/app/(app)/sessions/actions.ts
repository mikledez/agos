"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { backendFetch } from "@/lib/backend";

function requiredString(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

export async function createSession(formData: FormData): Promise<void> {
  const name = requiredString(formData, "name");
  if (!name) return;

  const parent = requiredString(formData, "parent_id");
  const response = await backendFetch("/sessions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      name,
      parent_id: parent ? Number(parent) : null,
    }),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  revalidatePath("/sessions");
}

export async function deleteSession(formData: FormData): Promise<void> {
  const sessionId = requiredString(formData, "session_id");
  const parentId = requiredString(formData, "parent_id");
  if (!sessionId) return;

  const response = await backendFetch(`/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    throw new Error(await response.text());
  }
  revalidatePath("/sessions");
  redirect(parentId ? `/sessions?session=${parentId}` : "/sessions");
}
