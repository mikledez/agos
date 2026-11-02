import Link from "next/link";
import LogoutButton from "./logout-button";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="header">
        <Link href="/analyzer" className="logo">
          AGOS
        </Link>
        <nav className="nav-links">
          <Link href="/analyzer">Analyzer</Link>
          <Link href="/sessions">Library</Link>
          <LogoutButton />
        </nav>
      </header>
      {children}
    </>
  );
}