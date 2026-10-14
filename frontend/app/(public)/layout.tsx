import Link from "next/link";

export default function PublicLayout({children} : {children: React.ReactNode}) {
  return (
    <>
      <header className="header">
        <Link href="/" className="logo">AGOS</Link>
        <nav>
          <Link href="/login" className="btn">Log in</Link>
        </nav>
      </header>
      {children}
    </>
  )
}