"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router       = useRouter();
  const token        = searchParams.get("token") ?? "";

  const [password,    setPassword]    = useState("");
  const [confirm,     setConfirm]     = useState("");
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");
  const [success,     setSuccess]     = useState(false);
  const [tokenValid,  setTokenValid]  = useState<boolean | null>(null);

  useEffect(() => {
    if (!token) { setTokenValid(false); return; }
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/reset-password/validate?token=${token}`)
      .then(r => r.json())
      .then(d => setTokenValid(d.valid))
      .catch(() => setTokenValid(false));
  }, [token]);

  async function handleReset() {
    setError("");
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm) { setError("Passwords don't match."); return; }
    setLoading(true);
    try {
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/reset-password`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Reset failed."); return; }
      setSuccess(true);
      setTimeout(() => router.push("/login"), 3000);
    } finally {
      setLoading(false);
    }
  }

  if (tokenValid === null) {
    return <p style={{ color: "#6b7280", fontSize: 13 }}>Validating link…</p>;
  }

  if (!tokenValid) {
    return (
      <div style={{ textAlign: "center" }}>
        <p style={{ fontSize: 24, marginBottom: 12 }}>⚠️</p>
        <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 16 }}>This reset link is invalid or has expired.</p>
        <button onClick={() => router.push("/forgot-password")} style={{ background: "none", border: "none", color: "#a78bfa", fontSize: 12, cursor: "pointer" }}>
          Request a new link
        </button>
      </div>
    );
  }

  if (success) {
    return (
      <div style={{ textAlign: "center" }}>
        <p style={{ fontSize: 24, marginBottom: 12 }}>✅</p>
        <p style={{ color: "#53c660", fontSize: 13 }}>Password reset! Redirecting to login…</p>
      </div>
    );
  }

  return (
    <>
      <h2 style={{ fontFamily: "var(--font-syne)", fontSize: 18, fontWeight: 700, color: "#F5F5F5", marginBottom: 8 }}>Set new password</h2>
      <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 20 }}>Choose a strong password for your GOATflow account.</p>
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="New password (8+ chars)"
        style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid #2A2A4A", borderRadius: 8, padding: "10px 12px", fontSize: 13, color: "#F5F5F5", outline: "none", marginBottom: 10, boxSizing: "border-box" }}
      />
      <input
        type="password"
        value={confirm}
        onChange={e => setConfirm(e.target.value)}
        placeholder="Confirm password"
        onKeyDown={e => e.key === "Enter" && handleReset()}
        style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid #2A2A4A", borderRadius: 8, padding: "10px 12px", fontSize: 13, color: "#F5F5F5", outline: "none", marginBottom: 10, boxSizing: "border-box" }}
      />
      {error && <p style={{ fontSize: 12, color: "#ef4444", marginBottom: 10 }}>{error}</p>}
      <button
        onClick={handleReset}
        disabled={loading}
        style={{ width: "100%", background: "#6100ff", border: "none", borderRadius: 8, padding: "11px 16px", fontSize: 13, fontWeight: 700, color: "white", cursor: loading ? "not-allowed" : "pointer" }}
      >
        {loading ? "Resetting…" : "Reset Password"}
      </button>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#08080f", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Image src="/icons/goatflow_main_screen_logo.webp" alt="GOATflow" width={200} height={200} style={{ width: 200, height: "auto", marginBottom: 24 }} />
      <div style={{ width: "100%", maxWidth: 360, background: "rgba(26,26,46,0.8)", border: "1px solid #2A2A4A", borderRadius: 12, padding: 24 }}>
        <Suspense fallback={<p style={{ color: "#6b7280" }}>Loading…</p>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
