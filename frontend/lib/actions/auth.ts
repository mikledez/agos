"use server";

import { signIn, signOut } from "@/auth";

export async function logout() {
  await signOut({ redirectTo: "/" });
}

export async function loginWithGoogle() {
  await signIn("google", { redirectTo: "/" });
}
