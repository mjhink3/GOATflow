"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useHerd } from "@/lib/hooks/useHerd";
import { useAuth } from "@/lib/hooks/useAuth";
import { sendBleat, getBleats, respondBleat, getBleatStats } from "@/lib/api/herds";

export default function HerdPage() {
  const router = useRouter();
  const { user } = useAuth();
  const currentUserId = user?.id ? String(user.id) : "";
  const { herd, members, stats, invite_code, isInHerd, isHerdBoss, isLoading } = useHerd();
  const qc = useQueryClient();

  const [bleatRecipient, setBleatRecipient] = useState("");
  const [bleatMessage, setBleatMessage] = useState("");
  const [isSendingBleat, setIsSendingBleat] = useState(false);

  const { data: bleatsData, refetch: refetchBleats } = useQuery({
    queryKey: ["bleats"],
    queryFn: getBleats,
    staleTime: 30_000,
    enabled: isInHerd,
  });

  const { data: bleatStats, refetch: refetchBleatStats } = useQuery({
    queryKey: ["bleat-stats"],
    queryFn: getBleatStats,
    staleTime: 60_000,
    enabled: isInHerd,
  });

  async function handleSendBleat() {
    if (!bleatRecipient) return;
    setIsSendingBleat(true);
    try {
      await sendBleat(bleatRecipient, bleatMessage || undefined);
      setBleatRecipient("");
      setBleatMessage("");
      qc.invalidateQueries({ queryKey: ["bleats"] });
      qc.invalidateQueries({ queryKey: ["bleat-stats"] });
    } catch (err) {
      console.error("[bleats] send failed:", err);
    } finally {
      setIsSendingBleat(false);
    }
  }

  async function handleRespondBleat(bleat_id: number) {
    try {
      const result = await respondBleat(bleat_id);
      qc.invalidateQueries({ queryKey: ["bleats"] });
      qc.invalidateQueries({ queryKey: ["bleat-stats"] });
      qc.invalidateQueries({ queryKey: ["player"] });
      window.alert(`🐐 Bleat responded! +${result.hay_earned} Hay earned (${result.speed_label} response)`);
    } catch (err) {
      console.error("[bleats] respond failed:", err);
    }
  }

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
      <button
        onClick={() => router.push("/dashboard")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontSize: 11, color: "#6b7280", background: "none", border: "none",
          cursor: "pointer", padding: 0, alignSelf: "flex-start", marginBottom: 16,
        }}
      >
        ← Back to Dashboard
      </button>

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
      <div style={{ marginBottom: 32 }}>
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

      {/* ── Bleats Section ── */}
      <section className="rounded-xl border border-goat-border p-4" style={{ background: "rgba(13,13,26,0.7)", marginBottom: 32 }}>
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>
          ▸ Bleats — Peer Accountability
        </p>

        {/* Send a Bleat */}
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 8 }}>
            Bleat a teammate to check in on their progress. They earn Hay for responding fast.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <select
              value={bleatRecipient}
              onChange={e => setBleatRecipient(e.target.value)}
              style={{
                background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)",
                borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#F5F5F5",
                outline: "none",
              }}
            >
              <option value="">Select a teammate to Bleat…</option>
              {members.filter(m => m.user_id !== currentUserId).map(m => (
                <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
              ))}
            </select>
            <input
              value={bleatMessage}
              onChange={e => setBleatMessage(e.target.value)}
              placeholder="Optional message… (e.g. 'Where are you at on the project?')"
              maxLength={120}
              style={{
                background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)",
                borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#F5F5F5",
                outline: "none",
              }}
            />
            <button
              onClick={handleSendBleat}
              disabled={!bleatRecipient || isSendingBleat}
              style={{
                background: bleatRecipient ? "rgba(97,0,255,0.35)" : "rgba(97,0,255,0.1)",
                border: "1px solid rgba(97,0,255,0.5)", borderRadius: 8,
                padding: "10px 16px", fontSize: 12, fontWeight: 700,
                color: "#a78bfa", cursor: bleatRecipient ? "pointer" : "not-allowed",
                textTransform: "uppercase", letterSpacing: "0.1em",
              }}
            >
              {isSendingBleat ? "Bleating…" : "🐐 Send Bleat"}
            </button>
          </div>
        </div>

        {/* Received Bleats */}
        {bleatsData?.received && bleatsData.received.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <p style={{ fontSize: 10, color: "#f59e0b", marginBottom: 8, fontWeight: 600 }}>
              📣 Bleats Received ({bleatsData.received.filter(b => !b.responded_at).length} pending)
            </p>
            {bleatsData.received.slice(0, 5).map(bleat => (
              <div key={bleat.id} style={{
                padding: "10px 12px", borderRadius: 8, marginBottom: 6,
                background: bleat.responded_at ? "rgba(83,198,96,0.06)" : "rgba(245,158,11,0.08)",
                border: `1px solid ${bleat.responded_at ? "rgba(83,198,96,0.2)" : "rgba(245,158,11,0.25)"}`,
                display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8,
              }}>
                <div>
                  <p style={{ fontSize: 12, color: "#F5F5F5", marginBottom: 2 }}>
                    🐐 <strong>{bleat.sender_name}</strong> bleated you
                  </p>
                  {bleat.message && <p style={{ fontSize: 11, color: "#9ca3af", fontStyle: "italic" }}>"{bleat.message}"</p>}
                  <p style={{ fontSize: 10, color: "#6b7280", marginTop: 2 }}>
                    {new Date(bleat.created_at).toLocaleDateString()}
                  </p>
                </div>
                {!bleat.responded_at ? (
                  <button
                    onClick={() => handleRespondBleat(bleat.id)}
                    style={{
                      background: "rgba(83,198,96,0.2)", border: "1px solid rgba(83,198,96,0.4)",
                      borderRadius: 6, padding: "6px 12px", fontSize: 11, fontWeight: 600,
                      color: "#53c660", cursor: "pointer", whiteSpace: "nowrap",
                    }}
                  >
                    Respond +Hay
                  </button>
                ) : (
                  <span style={{ fontSize: 10, color: "#53c660" }}>
                    ✓ +{bleat.response_hay_earned} Hay
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Bleat Stats */}
        {bleatStats && (
          <div style={{
            padding: "10px 12px", borderRadius: 8,
            background: "rgba(97,0,255,0.06)", border: "1px solid rgba(97,0,255,0.15)",
          }}>
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 6 }}>YOUR BLEAT STATS</p>
            <div style={{ display: "flex", gap: 16 }}>
              <div>
                <p style={{ fontSize: 16, fontWeight: 800, color: "#a78bfa" }}>{bleatStats.response_rate}%</p>
                <p style={{ fontSize: 9, color: "#6b7280" }}>Response Rate</p>
              </div>
              <div>
                <p style={{ fontSize: 16, fontWeight: 800, color: "#f59e0b" }}>{bleatStats.total_sent}</p>
                <p style={{ fontSize: 9, color: "#6b7280" }}>Bleats Sent</p>
              </div>
              <div>
                <p style={{ fontSize: 16, fontWeight: 800, color: "#53c660" }}>{bleatStats.total_responded}</p>
                <p style={{ fontSize: 9, color: "#6b7280" }}>Responded</p>
              </div>
              {bleatStats.avg_response_hours !== null && (
                <div>
                  <p style={{ fontSize: 16, fontWeight: 800, color: "#F5F5F5" }}>{bleatStats.avg_response_hours}h</p>
                  <p style={{ fontSize: 9, color: "#6b7280" }}>Avg Response</p>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Coming soon banner */}
      <div style={{ padding: "16px 20px", borderRadius: 12, background: "rgba(97,0,255,0.06)", border: "1px solid rgba(97,0,255,0.15)", textAlign: "center" }}>
        <p style={{ fontSize: 12, color: "#6b7280" }}>
          🏗️ <strong style={{ color: "#a78bfa" }}>Herd Dashboard</strong> — Full HerdBoss controls and Herd XP are coming in Phase 6.
        </p>
      </div>
    </div>
  );
}
