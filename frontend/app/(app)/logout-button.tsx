import { signOut } from "@/auth";

async function logout() {
  "use server";
  await signOut({ redirectTo: "/" });
}

export default function LogoutButton() {
  return (
    <form action={logout}>
      <button className="btn" type="submit">
        Logout
      </button>
    </form>
  );
}
