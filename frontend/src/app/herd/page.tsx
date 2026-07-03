"use client";

import { useRouter } from "next/navigation";
import { useHerd } from "@/lib/hooks/useHerd";
import { useAuth } from "@/lib/hooks/useAuth";
import { HerdBossView } from "@/components/herd/HerdBossView";
import { MemberView } from "@/components/herd/MemberView";

export default function HerdPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { herd, my_role, isLoading } = useHerd();

  if (!user) return null;

  if (isLoading) {
    return (
      <div className="min-h-screen goat-bg flex items-center justify-center">
        <div style={{ textAlign: "center" }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid rgba(97,0,255,0.2)", borderTopColor: "#6100ff", animation: "spin 0.9s linear infinite", margin: "0 auto 12px" }} />
          <p style={{ fontSize: 12, color: "#6b7280" }}>Loading herd…</p>
        </div>
      </div>
    );
  }

  if (!herd) {
    return (
      <div className="min-h-screen goat-bg flex items-center justify-center">
        <div style={{ textAlign: "center", maxWidth: 340, padding: "0 24px" }}>
          <p style={{ fontSize: 28, marginBottom: 12 }}>🐐</p>
          <h2 className="font-syne text-goat-white font-bold" style={{ fontSize: 20, marginBottom: 8 }}>No Herd Yet</h2>
          <p style={{ fontSize: 13, color: "#6b7280", lineHeight: 1.7, marginBottom: 24 }}>
            You&apos;re running solo. Start a herd to lead the charge, or join an existing one to run with a crew.
          </p>
          <button
            onClick={() => router.push("/dashboard")}
            style={{ background: "rgba(97,0,255,0.2)", border: "1px solid rgba(97,0,255,0.4)", borderRadius: 8, padding: "10px 20px", fontSize: 12, color: "#a78bfa", cursor: "pointer", fontWeight: 600 }}
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isHerdBoss = my_role === "herdboss";

  return (
    <div className="min-h-screen goat-bg">
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px 80px" }}>
        {/* Back to Dashboard */}
        <button
          onClick={() => router.push("/dashboard")}
          style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 24, background: "transparent", border: "none", cursor: "pointer", color: "#6b7280", fontSize: 12 }}
        >
          <span style={{ fontSize: 14 }}>←</span> Back to Dashboard
        </button>

        {isHerdBoss ? <HerdBossView /> : <MemberView />}
      </div>
    </div>
  );
}
