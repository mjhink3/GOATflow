"use client";

import { useHerd } from "@/lib/hooks/useHerd";

export default function HerdPage() {
  const { herd, members, stats, invite_code, isInHerd, isHerdBoss, isLoading } = useHerd();

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p style={{ color: "#6b7280", fontSize: 13 }}>Loading herd…</p>
      </div>
    );
  }

  if (!isInHerd) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 px-6">
        <p style={{ fontSize: 32 }}>🐐</p>
        <p className="font-syne text-goat-white font-bold" style={{ fontSize: 20 }}>You're not in a Herd yet</p>
        <p style={{ fontSize: 13, color: "#6b7280", textAlign: "center", maxWidth: 320 }}>
          Create or join a Herd from the sidebar to compete with your crew.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 px-6 py-8 max-w-2xl mx-auto w-full">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <h1 className="font-syne text-goat-white font-bold" style={{ fontSize: 28 }}>
            🐐 {herd?.name}
          </h1>
          {isHerdBoss && (
            <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 99, background: "rgba(97,0,255,0.3)", border: "1px solid rgba(97,0,255,0.5)", color: "#a78bfa", textTransform: "uppercase", letterSpacing: "0.1em" }}>
              HerdBoss
            </span>
          )}
        </div>
        {herd?.description && (
          <p style={{ fontSize: 13, color: "#6b7280" }}>{herd.description}</p>
        )}
        <p style={{ fontSize: 11, color: "#4b5563", marginTop: 4 }}>
          Pasture Level {herd?.pasture_level} · {herd?.herd_title}
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 32 }}>
          {[
            { label: "Total Hay", value: stats.total_hay_earned ?? 0, color: "#f59e0b" },
            { label: "Tracks Done", value: stats.total_tracks_completed ?? 0, color: "#53c660" },
            { label: "Members", value: stats.active_member_count ?? members.length, color: "#a78bfa" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: "rgba(13,13,26,0.8)", border: "1px solid #2A2A4A", borderRadius: 12, padding: "14px 16px", textAlign: "center" }}>
              <p style={{ fontSize: 22, fontWeight: 800, color, fontFamily: "var(--font-syne)" }}>{value}</p>
              <p style={{ fontSize: 10, color: "#6b7280", marginTop: 2 }}>{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Invite code (HerdBoss only) */}
      {isHerdBoss && invite_code && (
        <div style={{ background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)", borderRadius: 12, padding: "14px 16px", marginBottom: 32 }}>
          <p style={{ fontSize: 11, color: "#a78bfa", fontWeight: 600, marginBottom: 6 }}>Invite Code</p>
          <p style={{ fontSize: 13, fontFamily: "monospace", color: "#F5F5F5", letterSpacing: "0.1em" }}>{invite_code}</p>
          <p style={{ fontSize: 10, color: "#4b5563", marginTop: 4 }}>Share this with your crew so they can join from the sidebar.</p>
        </div>
      )}

      {/* Members leaderboard */}
      <div>
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>
          ▸ Herd Members
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {members.map((m, i) => (
            <div key={m.user_id} style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(13,13,26,0.6)", border: "1px solid #2A2A4A", borderRadius: 10, padding: "12px 16px" }}>
              <span style={{ fontSize: 13, color: "#4b5563", fontWeight: 700, width: 20, textAlign: "right", flexShrink: 0 }}>
                {i + 1}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 13, color: "#F5F5F5", fontWeight: 600, fontFamily: "var(--font-syne)" }}>
                    {m.display_name}
                  </span>
                  {m.role === "herdboss" && (
                    <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 99, background: "rgba(97,0,255,0.25)", color: "#a78bfa", border: "1px solid rgba(97,0,255,0.4)" }}>
                      Boss
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 10, color: "#6b7280", marginTop: 1 }}>
                  Lv {m.level ?? 1} · {m.tasks_completed ?? 0} tracks · {m.fresh_cheese ?? 0} 🧀
                </p>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <p style={{ fontSize: 13, color: "#f59e0b", fontWeight: 700 }}>{m.total_hay_earned ?? 0}</p>
                <p style={{ fontSize: 9, color: "#6b7280" }}>hay</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Coming soon banner */}
      <div style={{ marginTop: 40, padding: "16px 20px", borderRadius: 12, background: "rgba(97,0,255,0.06)", border: "1px solid rgba(97,0,255,0.15)", textAlign: "center" }}>
        <p style={{ fontSize: 12, color: "#6b7280" }}>
          🏗️ <strong style={{ color: "#a78bfa" }}>Herd Dashboard</strong> — Full HerdBoss controls, Bleats, and Herd XP are coming in Phase 6.
        </p>
      </div>
    </div>
  );
}
