"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/backend";
import type {
  ChatExchange,
  Folder,
  Humanization,
  SprintImage,
} from "@/lib/types";

export type ActionResult = { error?: string };

async function errorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
  } catch {
    // Ignore non-JSON error bodies.
  }
  return fallback;
}

function revalidateAll() {
  revalidatePath("/library");
  revalidatePath("/");
}

export async function createFolder(
  name: string,
  parentId: number | null,
): Promise<ActionResult & { folder?: Folder }> {
  const trimmed = name.trim();
  if (!trimmed) return { error: "Folder name is required" };

  const response = await backendFetch("/sessions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: trimmed, parent_id: parentId }),
  });
  if (!response.ok) {
    return { error: await errorMessage(response, "Could not create folder") };
  }
  revalidateAll();
  return { folder: (await response.json()) as Folder };
}

export async function renameFolder(
  folderId: number,
  name: string,
): Promise<ActionResult & { folder?: Folder }> {
  const trimmed = name.trim();
  if (!trimmed) return { error: "Folder name is required" };

  const response = await backendFetch(`/sessions/${folderId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: trimmed }),
  });
  if (!response.ok) {
    return { error: await errorMessage(response, "Could not rename folder") };
  }
  revalidateAll();
  return { folder: (await response.json()) as Folder };
}

export async function deleteFolder(folderId: number): Promise<ActionResult> {
  const response = await backendFetch(`/sessions/${folderId}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    return { error: await errorMessage(response, "Could not delete folder") };
  }
  revalidateAll();
  return {};
}

export async function renameImage(
  imageId: number,
  filename: string,
): Promise<ActionResult & { image?: SprintImage }> {
  const trimmed = filename.trim();
  if (!trimmed) return { error: "Image name is required" };

  const response = await backendFetch(`/images/${imageId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ original_filename: trimmed }),
  });
  if (!response.ok) {
    return { error: await errorMessage(response, "Could not rename image") };
  }
  revalidateAll();
  return { image: (await response.json()) as SprintImage };
}

export async function deleteImage(imageId: number): Promise<ActionResult> {
  const response = await backendFetch(`/images/${imageId}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    return { error: await errorMessage(response, "Could not delete image") };
  }
  revalidateAll();
  return {};
}

export async function generateFeedback(
  imageId: number,
): Promise<ActionResult & { humanization?: Humanization }> {
  const response = await backendFetch(
    `/images/${imageId}/humanization/generate`,
    { method: "POST" },
  );
  if (!response.ok) {
    return {
      error: await errorMessage(response, "Could not generate AI feedback"),
    };
  }
  revalidateAll();
  return { humanization: (await response.json()) as Humanization };
}

export async function sendChatMessage(
  imageId: number,
  content: string,
): Promise<ActionResult & { exchange?: ChatExchange }> {
  const trimmed = content.trim();
  if (!trimmed) return { error: "Write a question first" };
  if (trimmed.length > 1000) {
    return { error: "Questions must be 1,000 characters or fewer" };
  }

  const response = await backendFetch(`/images/${imageId}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content: trimmed }),
  });
  if (!response.ok) {
    return { error: await errorMessage(response, "Could not get an answer") };
  }
  return { exchange: (await response.json()) as ChatExchange };
}

export async function clearChat(imageId: number): Promise<ActionResult> {
  const response = await backendFetch(`/images/${imageId}/messages`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    return { error: await errorMessage(response, "Could not clear chat") };
  }
  return {};
}
