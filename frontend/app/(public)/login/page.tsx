"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json"},
            body: JSON.stringify({email, password}),
        });
        setLoading(false);
        if(res.ok) {
            router.push("/analyzer");
            router.refresh();
        } else {
            const data = await res.json().catch(() =>({}));
            setError(data.error || "Login failed");
        }
    }
    
    return (
        <main className="main">
            <form className="login" onSubmit={handleSubmit}>
                <label htmlFor="email">
                    Email
                </label>
                <input className="email_field" id="email" type="email" value={email} onChange={ (e) => setEmail(e.target.value)} required />
                <label htmlFor="password">
                    Password
                </label>
                <input className="pass_field" id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required/>
                {error && <p className="error">{error}</p>}
                <button type="submit" disabled={loading}>
                    {loading ? "Logging in..." : "Log in"}
                </button>
            </form>
        </main>
    )
}