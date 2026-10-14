import Link from "next/link";
import LogoutButton from "./logout-button";

export default function AppLayout({children}: {children: React.ReactNode}) {
    return (
        <>
            <header className="header">
                <Link href="/analyzer" className="logo">
                    AGOS
                </Link>
                <nav>
                    <LogoutButton />
                </nav>
            </header>
            {children}
        </>
    )
}