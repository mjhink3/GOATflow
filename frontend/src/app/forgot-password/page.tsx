"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function ForgotPasswordPage() {
  const [email, setEmail]       = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]   = useState(false);
  const router = useRouter();

  async function handleSubmit() {
    if (!email.trim()) return;
    setLoading(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#08080f", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Image src="/icons/goatflow_main_screen_logo.webp" alt="GOATflow" width={200} height={200} style={{ width: 200, height: "auto", marginBottom: 24 }} />

      {!submitted ? (
        <div style={{ width: "100%", maxWidth: 360, background: "rgba(26,26,46,0.8)", border: "1px solid #2A2A4A", borderRadius: 12, padding: 24 }}>
          <h2 style={{ fontFamily: "var(--font-syne)", fontSize: 18, fontWeight: 700, color: "#F5F5F5", marginBottom: 8 }}>Reset your password</h2>
          <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 20 }}>Enter the email on your account and we&apos;ll send a reset link.</p>

          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
            placeholder="your@email.com"
            style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid #2A2A4A", borderRadius: 8, padding: "10px 12px", fontSize: 13, color: "#F5F5F5", outline: "none", marginBottom: 16, boxSizing: "border-box" }}
          />

          <button
            onClick={handleSubmit}
            disabled={loading || !email.trim()}
            style={{ width: "100%", background: loading || !email.trim() ? "rgba(97,0,255,0.4)" : "#6100ff", border: "none", borderRadius: 8, padding: "11px 16px", fontSize: 13, fontWeight: 700, color: "white", cursor: loading || !email.trim() ? "not-allowed" : "pointer", marginBottom: 12 }}
          >
            {loading ? "Sending…" : "Send Reset Link"}
          </button>

          <button onClick={() => router.push("/login")} style={{ width: "100%", background: "none", border: "none", fontSize: 12, color: "#6b7280", cursor: "pointer" }}>
            ← Back to login
          </button>
        </div>
      ) : (
        <div style={{ width: "100%", maxWidth: 360, background: "rgba(26,26,46,0.8)", border: "1px solid #2A2A4A", borderRadius: 12, padding: 24, textAlign: "center" }}>
          <p style={{ fontSize: 24, marginBottom: 12 }}>📬</p>
          <h2 style={{ fontFamily: "var(--font-syne)", fontSize: 16, fontWeight: 700, color: "#F5F5F5", marginBottom: 8 }}>Check your inbox</h2>
          <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 20 }}>If that email exists in GOATflow, a reset link is on its way. Check your spam if you don&apos;t see it.</p>
          <button onClick={() => router.push("/login")} style={{ background: "none", border: "none", fontSize: 12, color: "#a78bfa", cursor: "pointer" }}>← Back to login</button>
        </div>
      )}
    </div>
  );
}
