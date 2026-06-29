"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useHerd } from "@/lib/hooks/useHerd";
import { useAuth } from "@/lib/hooks/useAuth";
import { sendBleat, getBleats, respondBleat, getBleatStats, BLEAT_TYPES, type Bleat } from "@/lib/api/herds";

const RESPONSE_OPTIONS = [
  { key: "quick",       label: "Quick 🐐",        hay: "10–20",  base: 10, needsText: false, desc: "Fast ack, no details needed" },
  { key: "deet",        label: "Drop a Deet 📝",  hay: "20–40",  base: 20, needsText: true,  desc: "1–2 sentence update" },
  { key: "goat_report", label: "GOAT Report 🏆",  hay: "35–70",  base: 35, needsText: true,  desc: "Full progress drop" },
];

function BleatCard({
  bleat,
  onRespond,
}: {
  bleat: Bleat;
  onRespond: (id: number, type: string, text?: string) => Promise<void>;
}) {
  const [selectedType, setSelectedType] = useState("");
  const [text, setText] = useState("");
  const [isResponding, setIsResponding] = useState(false);

  const bleatLabel = BLEAT_TYPES.find(t => t.key === bleat.bleat_type)?.label ?? bleat.bleat_type;

  async function submit() {
    if (!selectedType) return;
    const opt = RESPONSE_OPTIONS.find(o => o.key === selectedType)!;
    if (opt.needsText && !text.trim()) return;
    setIsResponding(true);
    await onRespond(bleat.id, selectedType, text.trim() || undefined);
    setIsResponding(false);
  }

  if (bleat.responded_at) {
    return (
      <div style={{
        padding: "10px 12px", borderRadius: 8, marginBottom: 6,
        background: "rgba(83,198,96,0.06)", border: "1px solid rgba(83,198,96,0.2)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
          <div>
            <p style={{ fontSize: 12, color: "#F5F5F5" }}>
              <strong>{bleat.sender_name}</strong> · {bleatLabel}
            </p>
            {bleat.response_text && (
              <p style={{ fontSize: 11, color: "#9ca3af", fontStyle: "italic", marginTop: 3 }}>
                "{bleat.response_text}"
              </p>
            )}
          </div>
          <span style={{ fontSize: 10, color: "#53c660", whiteSpace: "nowrap", flexShrink: 0 }}>
            ✓ +{bleat.response_hay_earned} Hay ({bleat.response_hay_tier})
          </span>
        </div>
      </div>
    );
  }

  const activeOpt = RESPONSE_OPTIONS.find(o => o.key === selectedType);

  return (
    <div style={{
      padding: "12px 14px", borderRadius: 8, marginBottom: 8,
      background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.25)",
    }}>
      <p style={{ fontSize: 13, color: "#F5F5F5", marginBottom: 2 }}>
        🐐 <strong>{bleat.sender_name}</strong> bleated you
      </p>
      <p style={{ fontSize: 12, color: "#f59e0b", marginBottom: 6 }}>{bleatLabel}</p>
      <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 10 }}>
        {new Date(bleat.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
      </p>

      {/* Response type buttons */}
      <div style={{ display: "flex", gap: 6, marginBottom: selectedType ? 8 : 0 }}>
        {RESPONSE_OPTIONS.map(opt => (
          <button
            key={opt.key}
            onClick={() => setSelectedType(selectedType === opt.key ? "" : opt.key)}
            style={{
              flex: 1, padding: "7px 4px", borderRadius: 7, fontSize: 10, fontWeight: 600,
              cursor: "pointer", textAlign: "center", lineHeight: 1.3,
              background: selectedType === opt.key ? "rgba(97,0,255,0.35)" : "rgba(97,0,255,0.08)",
              border: `1px solid ${selectedType === opt.key ? "rgba(97,0,255,0.6)" : "rgba(97,0,255,0.2)"}`,
              color: selectedType === opt.key ? "#a78bfa" : "#6b7280",
            }}
          >
            {opt.label}
            <br />
            <span style={{ fontSize: 9, color: "#f59e0b" }}>+{opt.hay} Hay</span>
          </button>
        ))}
      </div>

      {/* Text input for deet / goat_report */}
      {activeOpt?.needsText && (
        <div style={{ marginBottom: 8 }}>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={activeOpt.desc}
            rows={activeOpt.key === "goat_report" ? 3 : 2}
            maxLength={400}
            style={{
              width: "100%", background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)",
              borderRadius: 7, padding: "7px 10px", fontSize: 12, color: "#F5F5F5",
              outline: "none", resize: "none", boxSizing: "border-box",
            }}
          />
        </div>
      )}

      {selectedType && (
        <button
          onClick={submit}
          disabled={isResponding || (!!activeOpt?.needsText && !text.trim())}
          style={{
            width: "100%", padding: "8px 0", borderRadius: 7, fontSize: 12, fontWeight: 700,
            background: "rgba(83,198,96,0.25)", border: "1px solid rgba(83,198,96,0.45)",
            color: "#53c660", cursor: isResponding ? "not-allowed" : "pointer",
          }}
        >
          {isResponding ? "Responding…" : `Confirm Response (+${activeOpt?.hay} Hay)`}
        </button>
      )}
    </div>
  );
}

export default function HerdPage() {
  const router = useRouter();
  const { user } = useAuth();
  const currentUserId = user?.id ? String(user.id) : "";
  const { herd, members, stats, invite_code, isInHerd, isHerdBoss, isLoading } = useHerd();
  const qc = useQueryClient();

  const [bleatRecipient, setBleatRecipient] = useState("");
  const [selectedBleatType, setSelectedBleatType] = useState("");
  const [isSendingBleat, setIsSendingBleat] = useState(false);
  const [bleatSuccess, setBleatSuccess] = useState("");

  const { data: bleatsData } = useQuery({
    queryKey: ["bleats"],
    queryFn: getBleats,
    staleTime: 30_000,
    enabled: isInHerd,
  });

  const { data: bleatStats } = useQuery({
    queryKey: ["bleat-stats"],
    queryFn: getBleatStats,
    staleTime: 60_000,
    enabled: isInHerd,
  });

  async function handleSendBleat() {
    if (!bleatRecipient || !selectedBleatType) return;
    setIsSendingBleat(true);
    try {
      await sendBleat(bleatRecipient, selectedBleatType);
      setBleatRecipient("");
      setSelectedBleatType("");
      setBleatSuccess("Bleat sent! 🐐");
      setTimeout(() => setBleatSuccess(""), 3000);
      qc.invalidateQueries({ queryKey: ["bleats"] });
      qc.invalidateQueries({ queryKey: ["bleat-stats"] });
    } catch (err) {
      console.error("[bleats] send failed:", err);
    } finally {
      setIsSendingBleat(false);
    }
  }

  async function handleRespondBleat(bleat_id: number, response_type: string, response_text?: string) {
    const result = await respondBleat(bleat_id, response_type, response_text);
    qc.invalidateQueries({ queryKey: ["bleats"] });
    qc.invalidateQueries({ queryKey: ["bleat-stats"] });
    qc.invalidateQueries({ queryKey: ["player"] });
    window.alert(result.message);
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

  const pendingBleats = bleatsData?.received?.filter(b => !b.responded_at) ?? [];
  const respondedBleats = bleatsData?.received?.filter(b => !!b.responded_at) ?? [];

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

        {/* Received — pending first */}
        {pendingBleats.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 10, color: "#f59e0b", fontWeight: 600, marginBottom: 8 }}>
              📣 {pendingBleats.length} Bleat{pendingBleats.length !== 1 ? "s" : ""} waiting on you
            </p>
            {pendingBleats.map(bleat => (
              <BleatCard key={bleat.id} bleat={bleat} onRespond={handleRespondBleat} />
            ))}
          </div>
        )}

        {/* Send a Bleat */}
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 10, color: "#9ca3af", fontWeight: 600, marginBottom: 8 }}>SEND A BLEAT</p>
          <p style={{ fontSize: 11, color: "#6b7280", marginBottom: 10 }}>
            Bleat a teammate. They earn Hay for responding — more depth = more Hay.
          </p>

          {/* Recipient */}
          <select
            value={bleatRecipient}
            onChange={e => setBleatRecipient(e.target.value)}
            style={{
              width: "100%", background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)",
              borderRadius: 8, padding: "8px 12px", fontSize: 12, color: bleatRecipient ? "#F5F5F5" : "#6b7280",
              outline: "none", marginBottom: 10,
            }}
          >
            <option value="">Select a teammate…</option>
            {members.filter(m => m.user_id !== currentUserId).map(m => (
              <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
            ))}
          </select>

          {/* Bleat type grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 10 }}>
            {BLEAT_TYPES.map(bt => (
              <button
                key={bt.key}
                onClick={() => setSelectedBleatType(selectedBleatType === bt.key ? "" : bt.key)}
                style={{
                  padding: "8px 10px", borderRadius: 8, fontSize: 11, fontWeight: 600,
                  textAlign: "left", cursor: "pointer", lineHeight: 1.4,
                  background: selectedBleatType === bt.key ? "rgba(97,0,255,0.3)" : "rgba(97,0,255,0.07)",
                  border: `1px solid ${selectedBleatType === bt.key ? "rgba(97,0,255,0.6)" : "rgba(97,0,255,0.18)"}`,
                  color: selectedBleatType === bt.key ? "#a78bfa" : "#9ca3af",
                }}
              >
                {bt.label}
              </button>
            ))}
          </div>

          {bleatSuccess && (
            <p style={{ fontSize: 12, color: "#53c660", marginBottom: 8 }}>{bleatSuccess}</p>
          )}

          <button
            onClick={handleSendBleat}
            disabled={!bleatRecipient || !selectedBleatType || isSendingBleat}
            style={{
              width: "100%", padding: "10px 0", borderRadius: 8, fontSize: 12, fontWeight: 700,
              textTransform: "uppercase", letterSpacing: "0.08em",
              background: bleatRecipient && selectedBleatType ? "rgba(97,0,255,0.35)" : "rgba(97,0,255,0.08)",
              border: "1px solid rgba(97,0,255,0.5)", color: "#a78bfa",
              cursor: bleatRecipient && selectedBleatType ? "pointer" : "not-allowed",
            }}
          >
            {isSendingBleat ? "Bleating…" : "🐐 Send Bleat"}
          </button>
        </div>

        {/* Responded bleats (collapsed) */}
        {respondedBleats.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <p style={{ fontSize: 10, color: "#4b5563", fontWeight: 600, marginBottom: 6 }}>RECENT RESPONSES</p>
            {respondedBleats.slice(0, 3).map(bleat => (
              <BleatCard key={bleat.id} bleat={bleat} onRespond={handleRespondBleat} />
            ))}
          </div>
        )}

        {/* Bleat Stats */}
        {bleatStats && (
          <div style={{
            marginTop: 16, padding: "10px 12px", borderRadius: 8,
            background: "rgba(97,0,255,0.06)", border: "1px solid rgba(97,0,255,0.15)",
          }}>
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 8 }}>YOUR BLEAT STATS</p>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              {[
                { val: `${bleatStats.response_rate}%`, label: "Response Rate", color: "#a78bfa" },
                { val: bleatStats.total_sent,           label: "Bleats Sent",   color: "#f59e0b" },
                { val: bleatStats.total_responded,      label: "Responded",     color: "#53c660" },
                ...(bleatStats.avg_response_hours !== null
                  ? [{ val: `${bleatStats.avg_response_hours}h`, label: "Avg Response", color: "#F5F5F5" }]
                  : []),
                ...(bleatStats.avg_hay_per_response !== null
                  ? [{ val: `${bleatStats.avg_hay_per_response}`, label: "Avg Hay / Bleat", color: "#f59e0b" }]
                  : []),
              ].map(({ val, label, color }) => (
                <div key={label}>
                  <p style={{ fontSize: 16, fontWeight: 800, color }}>{val}</p>
                  <p style={{ fontSize: 9, color: "#6b7280" }}>{label}</p>
                </div>
              ))}
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
