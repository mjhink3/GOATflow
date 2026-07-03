"use client";

import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useHerd } from "@/lib/hooks/useHerd";
import {
  getDailyBrief, getBleats, respondBleat,
  BLEAT_TYPES, type DailyBriefMember, type RecentWin, type Bleat,
} from "@/lib/api/herds";
import { MountainProgress } from "@/components/ui/MountainProgress";

// ─── Constants ────────────────────────────────────────────────────────────────

const HERD_FENCE_THRESHOLDS = [0, 600, 2_000, 5_000, 12_000, 30_000, 100_000];
const HERD_PASTURE_NAMES    = ["The Pen", "The Grazing Grounds", "The Open Field", "The High Pasture", "The Summit Pasture", "The GOAT Range", "Beyond"];
const HERD_FENCE_NAMES      = ["Wooden Fence", "Stone Wall", "Iron Gate", "Mountain Pass", "Summit Gate", "The GOAT Horizon"];

const TIER_COLORS: Record<string, string> = {
  Micro: "#6b7280", Standard: "#3b82f6", "High-Leverage": "#8B5CF6", GOAT: "#FFD700",
};

const RESPONSE_OPTIONS = [
  { key: "quick",       label: "Quick 🐐",        hay: "10–20", needsText: false, desc: "Fast ack" },
  { key: "deet",        label: "Drop a Deet 📝",  hay: "20–40", needsText: true,  desc: "1–2 sentence update" },
  { key: "goat_report", label: "GOAT Report 🏆",  hay: "35–70", needsText: true,  desc: "Full progress drop" },
];

// ─── Helper functions ─────────────────────────────────────────────────────────

function memberStatus(m: DailyBriefMember): {
  label: string; textColor: string; circleColor: string; pulse: boolean;
} {
  if (m.cheese_state === "rotting")  return { label: "Rot Risk", textColor: "#f87171", circleColor: "#7f1d1d", pulse: true };
  if (m.hours_inactive >= 48)        return { label: "Cold",     textColor: "#ef4444", circleColor: "#ef4444", pulse: false };
  if (m.hours_inactive >= 24 || m.cheese_state === "staling")
    return { label: "Cooling", textColor: "#f59e0b", circleColor: "#f59e0b", pulse: false };
  if (m.hours_inactive < 6 && m.tracks_today > 0)
    return { label: "Hot",   textColor: "#53c660", circleColor: "#53c660", pulse: false };
  return   { label: "Fresh", textColor: "#a78bfa", circleColor: "#6100ff", pulse: false };
}

function herdMomentumStatus(members: DailyBriefMember[]): { label: string; color: string; herdStatus: string } {
  const total = members.length;
  if (!total) return { label: "No Data", color: "#6b7280", herdStatus: "No Members" };
  const cold      = members.filter(m => m.hours_inactive >= 48).length;
  const rotting   = members.filter(m => m.cheese_state === "rotting").length;
  const staling   = members.filter(m => m.cheese_state !== "fresh").length;
  const tracksToday = members.reduce((s, m) => s + m.tracks_today, 0);
  if (rotting > 0 || cold > total / 2) return { label: "Fence Watch", color: "#f87171", herdStatus: "Fence Watch" };
  if (staling > 0 || cold > 0)         return { label: "Staling",     color: "#f59e0b", herdStatus: "Momentum Staling" };
  if (tracksToday >= total * 2)         return { label: "Charging",    color: "#53c660", herdStatus: "Summit Push" };
  return                                       { label: "Steady",      color: "#86efac", herdStatus: "On Track" };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Sect({ label, children, accent, id }: {
  label: string; children: React.ReactNode; accent?: string; id?: string;
}) {
  return (
    <section id={id} className="rounded-xl border border-goat-border" style={{ background: "rgba(13,13,26,0.7)", padding: "16px", marginBottom: 20 }}>
      <p style={{ fontSize: 9, color: accent ?? "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 14 }}>▸ {label}</p>
      {children}
    </section>
  );
}

function PhaseBadge({ phase }: { phase: string }) {
  return (
    <span style={{ fontSize: 8, padding: "2px 6px", borderRadius: 99, background: "rgba(97,0,255,0.1)", color: "#4b5563", border: "1px solid rgba(97,0,255,0.15)", marginLeft: 6 }}>
      {phase}
    </span>
  );
}

function ToolCard({ icon, title, phase, children }: { icon: string; title: string; phase?: string; children: React.ReactNode }) {
  return (
    <div style={{ padding: "14px", borderRadius: 10, background: "rgba(13,13,26,0.6)", border: "1px solid #2A2A4A" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#F5F5F5" }}>{title}</p>
        {phase && <PhaseBadge phase={phase} />}
      </div>
      {children}
    </div>
  );
}

function LockedBtn({ label }: { label: string }) {
  return (
    <button disabled style={{ width: "100%", padding: "7px 0", borderRadius: 7, fontSize: 11, fontWeight: 600, background: "rgba(107,114,128,0.08)", border: "1px solid rgba(107,114,128,0.2)", color: "#4b5563", cursor: "not-allowed" }}>
      {label}
    </button>
  );
}

function SparkChart({ tracksToday }: { tracksToday: number }) {
  const bars = [0, 0, 0, 0, 0, 0, tracksToday];
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 12, marginTop: 6 }}>
      {bars.map((val, i) => {
        const isToday = i === 6;
        const barH = isToday && val > 0 ? 12 : 2;
        return (
          <div key={i} style={{
            width: 3, height: barH, borderRadius: 1, alignSelf: "flex-end",
            background: isToday && val > 0 ? "#53c660" : "rgba(255,255,255,0.08)",
          }} />
        );
      })}
    </div>
  );
}

function MiniBleatResponder({ bleat, onRespond }: {
  bleat: Bleat;
  onRespond: (id: number, type: string, text?: string) => Promise<void>;
}) {
  const [type, setType] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const opt = RESPONSE_OPTIONS.find(o => o.key === type);
  const bleatLabel = BLEAT_TYPES.find(t => t.key === bleat.bleat_type)?.label ?? bleat.bleat_type;

  return (
    <div style={{ padding: "10px 12px", borderRadius: 8, marginBottom: 8, background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)" }}>
      <p style={{ fontSize: 12, color: "#F5F5F5", marginBottom: 6 }}>
        🐐 <strong>{bleat.sender_name}</strong> — {bleatLabel}
      </p>
      <div style={{ display: "flex", gap: 5, marginBottom: type ? 8 : 0 }}>
        {RESPONSE_OPTIONS.map(o => (
          <button key={o.key} onClick={() => setType(type === o.key ? "" : o.key)} style={{
            flex: 1, padding: "5px 3px", borderRadius: 6, fontSize: 9, fontWeight: 600, cursor: "pointer", lineHeight: 1.3,
            background: type === o.key ? "rgba(97,0,255,0.35)" : "rgba(97,0,255,0.08)",
            border: `1px solid ${type === o.key ? "rgba(97,0,255,0.6)" : "rgba(97,0,255,0.2)"}`,
            color: type === o.key ? "#a78bfa" : "#6b7280",
          }}>
            {o.label}<br /><span style={{ fontSize: 8, color: "#f59e0b" }}>+{o.hay}</span>
          </button>
        ))}
      </div>
      {opt?.needsText && (
        <textarea value={text} onChange={e => setText(e.target.value)} placeholder={opt.desc} rows={2} maxLength={400} style={{
          width: "100%", background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)", borderRadius: 6,
          padding: "6px 10px", fontSize: 11, color: "#F5F5F5", outline: "none", resize: "none", boxSizing: "border-box", marginBottom: 6,
        }} />
      )}
      {type && (
        <button onClick={async () => {
          setLoading(true);
          await onRespond(bleat.id, type, text.trim() || undefined);
          setLoading(false); setType(""); setText("");
        }} disabled={loading || (!!opt?.needsText && !text.trim())} style={{
          width: "100%", padding: "6px 0", borderRadius: 6, fontSize: 11, fontWeight: 700,
          background: "rgba(83,198,96,0.25)", border: "1px solid rgba(83,198,96,0.45)", color: "#53c660", cursor: loading ? "not-allowed" : "pointer",
        }}>
          {loading ? "Responding…" : `Confirm (+${opt?.hay} Hay)`}
        </button>
      )}
    </div>
  );
}

// ─── HerdBossView ─────────────────────────────────────────────────────────────

export function HerdBossView() {
  const { herd, members, stats, invite_code } = useHerd();
  const qc = useQueryClient();
  const [standingsFilter, setStandingsFilter] = useState("all-time");

  const briefQuery = useQuery({
    queryKey: ["daily-brief"],
    queryFn: getDailyBrief,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const bleatsQuery = useQuery({
    queryKey: ["bleats"],
    queryFn: getBleats,
    staleTime: 30_000,
  });

  const data = briefQuery.data;
  const pendingBleats = bleatsQuery.data?.received?.filter(b => !b.responded_at) ?? [];

  async function handleRespondBleat(bleat_id: number, response_type: string, response_text?: string) {
    await respondBleat(bleat_id, response_type, response_text);
    qc.invalidateQueries({ queryKey: ["bleats"] });
    qc.invalidateQueries({ queryKey: ["player"] });
  }

  // Pasture progress
  const pastureLevel = herd?.pasture_level ?? 1;
  const levelIdx     = Math.max(0, pastureLevel - 1);
  const prevThresh   = HERD_FENCE_THRESHOLDS[levelIdx]     ?? 0;
  const nextThresh   = HERD_FENCE_THRESHOLDS[levelIdx + 1] ?? prevThresh + 1_000;
  const herdHay      = stats?.total_hay_earned
    ?? data?.members.reduce((s, m) => s + (m.total_hay ?? 0), 0)
    ?? 0;
  const hayInLevel   = Math.max(0, herdHay - prevThresh);
  const hayNeeded    = Math.max(1, nextThresh - prevThresh);
  const fencePct     = Math.min(100, Math.round(hayInLevel / hayNeeded * 100));
  const hayRemaining = Math.max(0, nextThresh - herdHay);
  const currPasture  = HERD_PASTURE_NAMES[levelIdx]     ?? "Unknown Pasture";
  const nextPasture  = HERD_PASTURE_NAMES[levelIdx + 1] ?? "The GOAT Range";
  const fenceName    = HERD_FENCE_NAMES[levelIdx]       ?? "The Next Fence";

  // KPI values
  const momentum    = herdMomentumStatus(data?.members ?? []);
  const tracksToday = data?.members.reduce((s, m) => s + m.tracks_today, 0) ?? 0;
  const hayToday    = data?.members.reduce((s, m) => s + m.hay_today, 0) ?? 0;
  const freshCount  = data?.members.filter(m => m.cheese_state === "fresh").length ?? 0;
  const coldCount   = data?.members.filter(m => m.hours_inactive >= 48).length ?? 0;
  const memberCount = data?.member_count ?? members.length;

  // Chronicle footer
  const totalTracks = members.reduce((s, m) => s + (m.tasks_completed ?? 0), 0);

  function scrollTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div>

      {/* ── 1. Herd Header ─────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
              <h1 className="font-syne text-goat-white font-bold" style={{ fontSize: 24 }}>🐐 {herd?.name}</h1>
              <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 99, background: "rgba(97,0,255,0.3)", border: "1px solid rgba(97,0,255,0.5)", color: "#a78bfa", textTransform: "uppercase", letterSpacing: "0.1em" }}>HerdBoss</span>
              {herd?.herd_type === "work" ? (
                <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 99, background: "rgba(59,130,246,0.2)", border: "1px solid rgba(59,130,246,0.4)", color: "#93c5fd" }}>💼 Work Herd</span>
              ) : (
                <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 99, background: "rgba(83,198,96,0.15)", border: "1px solid rgba(83,198,96,0.35)", color: "#86efac" }}>🌿 Free-Range</span>
              )}
              {herd?.is_verified && (
                <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 99, background: "rgba(245,158,11,0.2)", border: "1px solid rgba(245,158,11,0.45)", color: "#fcd34d" }}>✓ Verified</span>
              )}
            </div>
            <p style={{ fontSize: 11, color: "#6b7280" }}>Pasture Level {herd?.pasture_level} · {herd?.herd_title} · {members.length} Members</p>
            {herd?.description && <p style={{ fontSize: 12, color: "#4b5563", marginTop: 3 }}>{herd.description}</p>}
          </div>
          <div style={{ textAlign: "right", flexShrink: 0 }}>
            <p style={{ fontSize: 9, color: "#4b5563", marginBottom: 3 }}>Herd Status</p>
            <span style={{ fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 99, background: `${momentum.color}18`, border: `1px solid ${momentum.color}40`, color: momentum.color }}>
              {momentum.herdStatus}
            </span>
          </div>
        </div>
        {invite_code && (
          <div style={{ marginTop: 10, padding: "7px 12px", borderRadius: 8, background: "rgba(97,0,255,0.06)", border: "1px solid rgba(97,0,255,0.18)", display: "inline-flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 10, color: "#6b7280" }}>Invite:</span>
            <span style={{ fontSize: 12, fontFamily: "monospace", color: "#a78bfa", letterSpacing: "0.08em" }}>{invite_code}</span>
          </div>
        )}
      </div>

      {/* ── 2. Clear the Trail — command card ──────────────────────────────── */}
      <div className="rounded-xl border" style={{
        background: "linear-gradient(135deg, rgba(97,0,255,0.08) 0%, rgba(13,13,26,0.97) 100%)",
        borderColor: "rgba(97,0,255,0.25)",
        borderLeftWidth: 4,
        borderLeftColor: "#6100ff",
        padding: "20px 20px 20px 24px",
        marginBottom: 20,
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>🧭</span>
            <p style={{ fontSize: 14, fontWeight: 800, color: "#F5F5F5", fontFamily: "var(--font-syne)" }}>Clear the Trail</p>
          </div>
          <button onClick={() => briefQuery.refetch()} disabled={briefQuery.isRefetching} style={{
            background: "transparent", border: "1px solid rgba(97,0,255,0.2)", borderRadius: 6,
            padding: "4px 9px", fontSize: 10, color: "#4b5563",
            cursor: briefQuery.isRefetching ? "not-allowed" : "pointer",
          }}>
            {briefQuery.isRefetching ? "…" : "↻ Refresh"}
          </button>
        </div>

        {briefQuery.isLoading ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0" }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid rgba(97,0,255,0.2)", borderTopColor: "#6100ff", animation: "spin 0.8s linear infinite" }} />
            <p style={{ fontSize: 12, color: "#6b7280" }}>Analyzing your herd…</p>
          </div>
        ) : data ? (
          <>
            <p style={{ fontSize: 16, color: "#e5e7eb", lineHeight: 1.8, marginBottom: 20, fontStyle: "italic" }}>
              &ldquo;{data.brief}&rdquo;
            </p>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {[
                { label: "Send Herd Call",     id: "herdboss-tools", color: "#6100ff", bg: "rgba(97,0,255,0.18)" },
                { label: "View Member Health", id: "member-health",  color: "#53c660", bg: "rgba(83,198,96,0.1)" },
              ].map(btn => (
                <button key={btn.label} onClick={() => scrollTo(btn.id)} style={{
                  padding: "7px 14px", borderRadius: 7, fontSize: 11, fontWeight: 600, cursor: "pointer",
                  background: btn.bg, border: `1px solid ${btn.color}44`, color: btn.color,
                }}>
                  {btn.label}
                </button>
              ))}
            </div>
          </>
        ) : null}
      </div>

      {/* ── 3. KPI Strip ───────────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))", gap: 8, marginBottom: 20 }}>
        {[
          { label: "Herd Momentum",  value: momentum.label,                                                    color: momentum.color },
          { label: "Hay Today",      value: hayToday.toLocaleString(),                                         color: "#f59e0b" },
          { label: "Tracks Cleared", value: tracksToday.toString(),                                            color: "#53c660" },
          { label: "Fresh Members",  value: `${freshCount}/${memberCount}`,                                    color: "#86efac" },
          { label: "Cold Members",   value: coldCount.toString(),                                              color: coldCount > 0 ? "#f87171" : "#6b7280" },
          { label: "Open Decisions", value: "0",                                                               color: "#6b7280" },
          { label: "Next Fence",     value: hayRemaining > 0 ? `${hayRemaining.toLocaleString()} Hay` : "Cleared", color: "#a78bfa" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ padding: "10px", borderRadius: 10, background: "rgba(13,13,26,0.7)", border: "1px solid #2A2A4A", textAlign: "center" }}>
            <p style={{ fontSize: 13, fontWeight: 800, color, fontFamily: "var(--font-syne)", lineHeight: 1.2 }}>{value}</p>
            <p style={{ fontSize: 8, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 3 }}>{label}</p>
          </div>
        ))}
      </div>

      {/* ── 4. Member Health — visual status grid ──────────────────────────── */}
      <Sect label="Member Health" id="member-health">
        {!data ? (
          <p style={{ fontSize: 12, color: "#4b5563", padding: "8px 0" }}>Loading member data…</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3" style={{ gap: 10 }}>
            {data.members.map(m => {
              const status = memberStatus(m);
              const isCritical = m.hours_inactive >= 48 || m.cheese_state === "rotting";
              const borderColor = isCritical
                ? "rgba(239,68,68,0.3)"
                : m.hours_inactive >= 24 ? "rgba(245,158,11,0.2)"
                : "#2A2A4A";
              return (
                <div key={m.user_id} style={{
                  padding: "16px 12px 12px", borderRadius: 12,
                  background: "rgba(13,13,26,0.5)", border: `1px solid ${borderColor}`,
                  display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center",
                }}>
                  {/* Status circle */}
                  <div
                    className={status.pulse ? "animate-pulse" : ""}
                    style={{
                      width: 40, height: 40, borderRadius: "50%",
                      background: status.circleColor, marginBottom: 8, flexShrink: 0,
                      boxShadow: `0 0 14px ${status.circleColor}60`,
                    }}
                  />
                  {/* Name */}
                  <p style={{ fontSize: 12, fontWeight: 700, color: "#F5F5F5", fontFamily: "var(--font-syne)", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "100%" }}>
                    {m.name}
                    {m.role === "herdboss" && <span style={{ fontSize: 8, color: "#a78bfa", marginLeft: 4 }}>Boss</span>}
                  </p>
                  {/* Status label */}
                  <p style={{ fontSize: 10, fontWeight: 600, color: status.textColor, marginBottom: 4 }}>{status.label}</p>
                  {/* Stats */}
                  <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 2 }}>
                    {m.tracks_today} tracks · +{m.hay_today} Hay
                  </p>
                  {/* Last active */}
                  <p style={{ fontSize: 9, color: "#4b5563" }}>
                    {m.hours_inactive < 999 ? `${m.hours_inactive}h ago` : "No activity"}
                  </p>
                  {/* 7-day spark */}
                  <SparkChart tracksToday={m.tracks_today} />
                  {/* Herd Call shortcut for cold/rot members */}
                  {isCritical && (
                    <button onClick={() => scrollTo("herdboss-tools")} style={{
                      marginTop: 10, width: "100%", padding: "5px 0", borderRadius: 6,
                      fontSize: 10, fontWeight: 600, cursor: "pointer",
                      background: "rgba(97,0,255,0.12)", border: "1px solid rgba(97,0,255,0.3)", color: "#a78bfa",
                    }}>
                      📡 Send Herd Call ↓
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Sect>

      {/* ── 5. Pasture Progress ────────────────────────────────────────────── */}
      <Sect label="Pasture Progress">
        <MountainProgress
          currentLevel={herd?.pasture_level ?? 1}
          currentHay={herdHay}
          hayToNext={hayRemaining}
          memberPositions={data?.members.map(m => ({
            display_name: m.name,
            level: m.level,
          }))}
        />
      </Sect>

      {/* ── 6. HerdBoss Tools ──────────────────────────────────────────────── */}
      <Sect label="HerdBoss Tools" id="herdboss-tools">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>

          <ToolCard icon="📡" title="Herd Call" phase="Phase 7">
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 10, lineHeight: 1.6 }}>Standard leadership communication. 2 per week max. Unspent calls generate Salt.</p>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Used this week</span>
              <span style={{ fontSize: 11, color: "#F5F5F5", fontWeight: 600 }}>0 / 2</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Response rate</span>
              <span style={{ fontSize: 11, color: "#6b7280" }}>—</span>
            </div>
            <LockedBtn label="Send Herd Call" />
          </ToolCard>

          <ToolCard icon="📯" title="Horn Blast" phase="Phase 7">
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 10, lineHeight: 1.6 }}>Emergency tool. Unlocks near fence threshold or regression risk only.</p>
            <div style={{ padding: "5px 8px", borderRadius: 6, background: "rgba(107,114,128,0.08)", border: "1px solid rgba(107,114,128,0.15)", marginBottom: 8 }}>
              <p style={{ fontSize: 10, color: "#6b7280", textAlign: "center" }}>🔒 Locked — no fence threat detected</p>
            </div>
            <p style={{ fontSize: 9, color: "#4b5563", lineHeight: 1.7, marginBottom: 10 }}>
              Penalty ladder: 1st −3 · 2nd −6 · 3rd −12 · 4th+ −24 composite
            </p>
            <LockedBtn label="Unavailable" />
          </ToolCard>

          <ToolCard icon="⚡" title="Rally Cry" phase="Phase 7">
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 10, lineHeight: 1.6 }}>Earned leadership tool. Granted monthly based on Herd freshness and engagement.</p>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Balance</span>
              <span style={{ fontSize: 11, color: "#F5F5F5", fontWeight: 600 }}>0 available</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Response rate</span>
              <span style={{ fontSize: 11, color: "#6b7280" }}>—</span>
            </div>
            <LockedBtn label="Deploy Rally Cry" />
          </ToolCard>

          <ToolCard icon="🧂" title="Salt" phase="Phase 7">
            <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 12, lineHeight: 1.6 }}>
              Earned when your Herd performs without extra pushes. Leadership restraint — the rarest stat.
            </p>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>This month</span>
              <span style={{ fontSize: 15, color: "#FFD700", fontWeight: 800, fontFamily: "var(--font-syne)" }}>0</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontSize: 11, color: "#9ca3af" }}>Lifetime Salt</span>
              <span style={{ fontSize: 11, color: "#6b7280" }}>0</span>
            </div>
          </ToolCard>
        </div>
      </Sect>

      {/* ── Pending Bleats (respond only, shown when present) ──────────────── */}
      {pendingBleats.length > 0 && (
        <Sect label={`Bleats Awaiting Your Response (${pendingBleats.length})`} accent="#f59e0b">
          <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 10 }}>
            Members can bleat you. Respond to earn Hay — HerdBosses use Herd Calls and Rally Cries to initiate.
          </p>
          {pendingBleats.map(bleat => (
            <MiniBleatResponder key={bleat.id} bleat={bleat} onRespond={handleRespondBleat} />
          ))}
        </Sect>
      )}

      {/* ── 7. Recent Wins ─────────────────────────────────────────────────── */}
      <Sect label="Recent Wins (last 24h)">
        {!data || data.recent_wins.length === 0 ? (
          <p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "8px 0" }}>No wins yet today. The pasture is waiting.</p>
        ) : (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {data.recent_wins.slice(0, 5).map((w: RecentWin, i: number) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", borderRadius: 7, background: "rgba(83,198,96,0.04)", border: "1px solid rgba(83,198,96,0.1)" }}>
                  <span style={{ fontSize: 10, color: "#53c660", flexShrink: 0 }}>✓</span>
                  <div style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "#F5F5F5" }}>{w.member_name}</span>
                    <span style={{ fontSize: 11, color: "#6b7280" }}> — {w.task_name}</span>
                  </div>
                  <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 99, flexShrink: 0, background: `${TIER_COLORS[w.xp_tier] ?? "#6b7280"}18`, border: `1px solid ${TIER_COLORS[w.xp_tier] ?? "#6b7280"}40`, color: TIER_COLORS[w.xp_tier] ?? "#6b7280", fontWeight: 600 }}>
                    {w.xp_tier}
                  </span>
                  <span style={{ fontSize: 11, color: "#f59e0b", fontWeight: 600, flexShrink: 0 }}>+{w.hay_earned}</span>
                </div>
              ))}
            </div>
            {data.recent_wins.length > 5 && (
              <p style={{ fontSize: 11, color: "#4b5563", marginTop: 8, textAlign: "center" }}>
                View all {data.recent_wins.length} wins ↓
              </p>
            )}
          </>
        )}
      </Sect>

      {/* ── 8. Herd Standings ──────────────────────────────────────────────── */}
      <Sect label="Herd Standings">
        <div style={{ display: "flex", gap: 6, marginBottom: 12, flexWrap: "wrap" }}>
          {[
            { key: "all-time",  label: "All-time",  live: true  },
            { key: "this-week", label: "This Week", live: false },
            { key: "today",     label: "Today",     live: false },
          ].map(f => (
            <button key={f.key} onClick={() => f.live && setStandingsFilter(f.key)} style={{
              padding: "4px 10px", borderRadius: 99, fontSize: 10, fontWeight: 600, cursor: f.live ? "pointer" : "not-allowed",
              background: standingsFilter === f.key ? "rgba(97,0,255,0.25)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${standingsFilter === f.key ? "rgba(97,0,255,0.5)" : "rgba(255,255,255,0.08)"}`,
              color: standingsFilter === f.key ? "#a78bfa" : "#4b5563",
            }}>
              {f.label}{!f.live && <PhaseBadge phase="Soon" />}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {members.map((m, i) => (
            <div key={m.user_id} style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(13,13,26,0.5)", border: "1px solid #2A2A4A", borderRadius: 10, padding: "10px 14px" }}>
              <span style={{ fontSize: 12, color: "#4b5563", fontWeight: 700, width: 20, textAlign: "center", flexShrink: 0 }}>{i + 1}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 13, color: "#F5F5F5", fontWeight: 600, fontFamily: "var(--font-syne)" }}>{m.display_name}</span>
                  {m.role === "herdboss" && (
                    <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 99, background: "rgba(97,0,255,0.25)", color: "#a78bfa", border: "1px solid rgba(97,0,255,0.4)" }}>Boss</span>
                  )}
                </div>
                <p style={{ fontSize: 10, color: "#6b7280", marginTop: 1 }}>Lv {m.level ?? 1} · {m.tasks_completed ?? 0} tracks · {m.fresh_cheese ?? 0} 🧀</p>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <p style={{ fontSize: 13, color: "#f59e0b", fontWeight: 700 }}>{(m.total_hay_earned ?? 0).toLocaleString()}</p>
                <p style={{ fontSize: 9, color: "#6b7280" }}>Hay</p>
              </div>
            </div>
          ))}
        </div>
      </Sect>

      {/* ── 9. Chronicle footer ────────────────────────────────────────────── */}
      <p style={{ fontSize: 11, color: "#374151", textAlign: "center", paddingTop: 4, paddingBottom: 32 }}>
        📖 Chronicle moments: Herd formed · {herdHay.toLocaleString()} Hay stacked · {totalTracks} tracks cleared
      </p>

    </div>
  );
}
