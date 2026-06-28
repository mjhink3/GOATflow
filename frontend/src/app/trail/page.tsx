"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { usePlayer } from "@/lib/hooks/usePlayer";
import { getLog, type LogFilter } from "@/lib/api/log";
import type { OperationalLogEntry } from "@/lib/types";

const WEEK_LABELS = ["Wk -3", "Wk -2", "Wk -1", "This Wk"];

const FILTER_TABS: { key: LogFilter; label: string }[] = [
  { key: "all",       label: "All"       },
  { key: "completed", label: "Completed" },
  { key: "dismissed", label: "Dismissed" },
  { key: "reordered", label: "Reordered" },
];

const ACHIEVEMENTS: { id: string; tier: number; name: string; desc: string; hint: string }[] = [
  // Tier 1
  { id: "first_blood",      tier: 1, name: "First Blood",         desc: "Complete your first Track",                      hint: "Complete 1 Track" },
  { id: "the_opener",       tier: 1, name: "The Opener",          desc: "Complete 5 Tracks in a single day",              hint: "5 Tracks in one day" },
  { id: "stake_your_claim", tier: 1, name: "Stake Your Claim",    desc: "Honor your Morning Stake 3 days in a row",       hint: "3-day Stake streak" },
  { id: "voice_of_the_goat",tier: 1, name: "Voice of the Goat",  desc: "Use Voice Drop to create a Track",               hint: "Use the mic button" },
  // Tier 2
  { id: "the_grind",        tier: 2, name: "The Grind",           desc: "Maintain a 7-day GAIT streak",                  hint: "7 consecutive days" },
  { id: "iron_commitment",  tier: 2, name: "Iron Commitment",     desc: "Honor Morning Stake 14 days in a row",           hint: "14-day Stake streak" },
  { id: "clip_master",      tier: 2, name: "Clip Master",         desc: "Hit 90%+ Clip Rate for a full week",             hint: "90%+ this week" },
  { id: "horn_whisperer",   tier: 2, name: "Horn Whisperer",      desc: "Have a Horn influence 10+ Tracks",               hint: "10 Horn-influenced Tracks" },
  // Tier 3
  { id: "fresh_cheese_factory", tier: 3, name: "Fresh Cheese Factory", desc: "Bank 10 Fresh Cheese",                    hint: "500 × 10 Hay earned" },
  { id: "the_hard_way",     tier: 3, name: "The Hard Way",        desc: "Complete a GOAT-tier Track within 24 hours",     hint: "GOAT tier, same day" },
  { id: "know_thyself",     tier: 3, name: "Know Thyself",        desc: "Add Trail Notes to 20 completed Tracks",         hint: "20 Trail Notes saved" },
  { id: "zero_bull",        tier: 3, name: "Zero Bull",           desc: "Complete 50 Tracks with 0 cancelled",            hint: "50 completions, no cancels" },
];

const TIER_LABELS: Record<number, string> = {
  1: "TIER 1 — EARLY WINS",
  2: "TIER 2 — CONSISTENCY",
  3: "TIER 3 — MASTERY",
};

type TrailNoteMap = Record<string, { question: string; note: string; timestamp: number; taskName: string }>;
type CancelReasonMap = Record<string, { reason: string; taskName: string; timestamp: number }>;

function resolutionBadge(resolution: string) {
  if (resolution === "completed") {
    return (
      <span style={{
        fontSize: 9, padding: "2px 8px", borderRadius: 99, textTransform: "uppercase",
        background: "rgba(83,198,96,0.12)", border: "1px solid rgba(83,198,96,0.35)",
        color: "#53c660", fontWeight: 600, letterSpacing: "0.08em",
      }}>Completed</span>
    );
  }
  if (resolution === "cancelled" || resolution === "dismissed") {
    return (
      <span style={{
        fontSize: 9, padding: "2px 8px", borderRadius: 99, textTransform: "uppercase",
        background: "rgba(107,114,128,0.12)", border: "1px solid rgba(107,114,128,0.3)",
        color: "#9ca3af", fontWeight: 600, letterSpacing: "0.08em",
      }}>Cancelled</span>
    );
  }
  return (
    <span style={{
      fontSize: 9, padding: "2px 8px", borderRadius: 99, textTransform: "uppercase",
      background: "rgba(245,158,11,0.12)", border: "1px solid rgba(245,158,11,0.3)",
      color: "#f59e0b", fontWeight: 600, letterSpacing: "0.08em",
    }}>Reordered</span>
  );
}

function fmtDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function daysElapsed(loggedAt: string | null, resolvedAt: string) {
  const start = loggedAt ? new Date(loggedAt) : new Date(resolvedAt);
  const end = new Date(resolvedAt);
  const diff = Math.max(0, Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)));
  return diff;
}

function ClipBar({ pct }: { pct: number | null }) {
  if (pct === null) {
    return (
      <span style={{ fontFamily: "monospace", color: "#4b5563", letterSpacing: "0.05em" }}>
        {"░".repeat(10)}<span style={{ color: "#6b7280", marginLeft: 6 }}>—</span>
      </span>
    );
  }
  const filled = Math.min(10, Math.max(0, Math.round(pct / 10)));
  const color = pct >= 75 ? "#53c660" : pct >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <span style={{ fontFamily: "monospace", color, letterSpacing: "0.05em" }}>
      {"█".repeat(filled)}{"░".repeat(10 - filled)}
      <span style={{ color: "#9ca3af", marginLeft: 6 }}>{pct}%</span>
    </span>
  );
}

function LogEntryCard({ entry, trailNotes, cancelReasons, onNotesChanged }: {
  entry: OperationalLogEntry;
  trailNotes: TrailNoteMap;
  cancelReasons: CancelReasonMap;
  onNotesChanged: (notes: TrailNoteMap) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draftNote, setDraftNote] = useState("");
  const noteKey = String(entry.id);
  const existingNote = trailNotes[noteKey];
  const cancelReason = entry.resolution === "cancelled" ? cancelReasons[noteKey]?.reason : undefined;
  const elapsed = daysElapsed(entry.logged_at, entry.resolved_at);

  function saveNote() {
    const trimmed = draftNote.trim();
    if (!trimmed) return;
    const updated = {
      ...trailNotes,
      [noteKey]: {
        question: "",
        note: trimmed,
        timestamp: Date.now(),
        taskName: entry.task_name,
      },
    };
    localStorage.setItem("goatflow_trail_notes", JSON.stringify(updated));
    onNotesChanged(updated);
    setEditing(false);
    setDraftNote("");
  }

  function startEdit() {
    setDraftNote(existingNote?.note ?? "");
    setEditing(true);
  }

  return (
    <div
      className="rounded-xl border border-goat-border"
      style={{ background: "rgba(26,26,46,0.5)", padding: "14px 16px" }}
    >
      {/* Top row: task name + badge */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <p className="font-syne font-bold text-goat-white" style={{ fontSize: 13, lineHeight: 1.3 }}>
          {entry.task_name}
        </p>
        {resolutionBadge(entry.resolution)}
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mb-2">
        {entry.logged_at && (
          <span style={{ fontSize: 10, color: "#6b7280" }}>Logged: {fmtDate(entry.logged_at)}</span>
        )}
        <span style={{ fontSize: 10, color: "#6b7280" }}>Resolved: {fmtDate(entry.resolved_at)}</span>
        <span style={{ fontSize: 10, color: "#9ca3af" }}>
          {elapsed === 0 ? "Same day" : elapsed === 1 ? "1 day" : `${elapsed} days`}
        </span>
        {entry.resolution === "completed" && entry.hay_earned > 0 && (
          <span style={{ fontSize: 10, color: "#f59e0b", fontWeight: 600 }}>+{entry.hay_earned} Hay 🌾</span>
        )}
      </div>

      {/* Horn attribution */}
      {entry.horn_applied_name && (
        <p style={{ fontSize: 10, color: "#a78bfa", fontStyle: "italic", marginBottom: 8 }}>
          ◆ {entry.horn_applied_name}
        </p>
      )}

      {/* Cancel reason */}
      {cancelReason && (
        <p style={{ fontSize: 11, color: "#9ca3af", fontStyle: "italic", marginBottom: 8 }}>
          Reason: {cancelReason}
        </p>
      )}

      {/* Trail note */}
      {existingNote && !editing && (
        <div
          className="rounded-lg"
          style={{ background: "rgba(97,0,255,0.07)", border: "1px solid rgba(97,0,255,0.2)", padding: "8px 10px", marginBottom: 6 }}
        >
          <p style={{ fontSize: 11, color: "#c4b5fd", lineHeight: 1.5 }}>{existingNote.note}</p>
        </div>
      )}

      {editing && (
        <div style={{ marginBottom: 6 }}>
          <textarea
            value={draftNote}
            onChange={e => setDraftNote(e.target.value.slice(0, 200))}
            rows={2}
            autoFocus
            style={{
              width: "100%", background: "rgba(97,0,255,0.07)", border: "1px solid rgba(97,0,255,0.3)",
              borderRadius: 8, padding: "8px 10px", fontSize: 11, color: "#F5F5F5",
              outline: "none", resize: "none", fontFamily: "inherit", boxSizing: "border-box",
            }}
          />
          <div className="flex gap-2 mt-1">
            <button
              onClick={saveNote}
              style={{
                fontSize: 10, padding: "4px 12px", borderRadius: 6, fontWeight: 600,
                background: "rgba(97,0,255,0.3)", border: "1px solid rgba(97,0,255,0.5)",
                color: "#a78bfa", cursor: "pointer",
              }}
            >Save</button>
            <button
              onClick={() => setEditing(false)}
              style={{
                fontSize: 10, padding: "4px 10px", borderRadius: 6,
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)",
                color: "#6b7280", cursor: "pointer",
              }}
            >Cancel</button>
          </div>
        </div>
      )}

      {!editing && (
        <button
          onClick={startEdit}
          style={{
            fontSize: 9, color: "#6b7280", background: "none", border: "none",
            cursor: "pointer", padding: 0, textDecoration: "underline",
          }}
        >
          {existingNote ? "Edit note" : "Add note"}
        </button>
      )}
    </div>
  );
}

export default function TrailPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<LogFilter>("all");
  const [trailNotes, setTrailNotes] = useState<TrailNoteMap>({});
  const [cancelReasons, setCancelReasons] = useState<CancelReasonMap>({});
  const [unlockedAchievements, setUnlockedAchievements] = useState<string[]>([]);
  const { player } = usePlayer();

  const { data: entries = [], isLoading, isError } = useQuery<OperationalLogEntry[]>({
    queryKey: ["log", filter],
    queryFn: () => getLog(filter),
    retry: 1,
  });

  useEffect(() => {
    try {
      const raw = localStorage.getItem("goatflow_trail_notes");
      if (raw) setTrailNotes(JSON.parse(raw));
    } catch { /* ignore */ }

    try {
      const raw = localStorage.getItem("goatflow_cancel_reasons");
      if (raw) setCancelReasons(JSON.parse(raw));
    } catch { /* ignore */ }

    try {
      const raw = localStorage.getItem("goatflow_achievements");
      if (raw) setUnlockedAchievements(JSON.parse(raw));
    } catch { /* ignore */ }
  }, []);

  const weeklyRates: (number | null)[] = player?.weekly_clip_rates?.length
    ? player.weekly_clip_rates.map(r => r != null ? Math.round(r * 100) : null)
    : [null, null, null, null];

  const playbookInsights = useMemo(() => {
    if (!entries.length) return [];
    const byCategory: Record<string, { note: string; taskName: string; category: string; timestamp: number }> = {};
    for (const entry of entries) {
      const note = trailNotes[String(entry.id)];
      if (note?.note && entry.category) {
        const cat = entry.category;
        if (!byCategory[cat] || note.timestamp > byCategory[cat].timestamp) {
          byCategory[cat] = { note: note.note, taskName: entry.task_name, category: cat, timestamp: note.timestamp };
        }
      }
    }
    return Object.values(byCategory).sort((a, b) => b.timestamp - a.timestamp).slice(0, 3);
  }, [entries, trailNotes]);

  return (
    <div className="flex flex-col gap-6 px-6 py-6 pb-16 max-w-3xl mx-auto w-full">

      {/* Back button */}
      <button
        onClick={() => router.push("/dashboard")}
        style={{
          display: "flex", alignItems: "center", gap: 5,
          fontSize: 12, color: "#9ca3af", background: "none", border: "none",
          cursor: "pointer", padding: 0, alignSelf: "flex-start",
          transition: "color 0.15s",
        }}
        onMouseEnter={e => (e.currentTarget.style.color = "#a78bfa")}
        onMouseLeave={e => (e.currentTarget.style.color = "#9ca3af")}
      >
        ← Back to Dashboard
      </button>

      {/* Header */}
      <div className="flex items-center gap-3">
        <Image src="/icons/icon_trail_notes.webp" alt="" width={28} height={28} />
        <h1 className="font-syne font-bold text-goat-white" style={{ fontSize: 22 }}>Trail Notes</h1>
      </div>

      {/* Playbook Insights */}
      {playbookInsights.length > 0 && (
        <section
          className="rounded-xl border border-goat-border"
          style={{ background: "rgba(97,0,255,0.04)", padding: "14px 16px" }}
        >
          <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 10 }}>
            ▸ Playbook Insights
          </p>
          <div className="flex flex-col gap-3">
            {playbookInsights.map((insight, i) => (
              <div key={i}>
                <p style={{ fontSize: 10, color: "#6b7280", marginBottom: 2, textTransform: "capitalize" }}>
                  Last time you had a <span style={{ color: "#a78bfa" }}>{insight.category}</span> task:
                </p>
                <p style={{ fontSize: 12, color: "#c4b5fd", fontStyle: "italic", lineHeight: 1.5 }}>
                  &ldquo;{insight.note}&rdquo;
                </p>
                <p style={{ fontSize: 10, color: "#4b5563", marginTop: 2 }}>{insight.taskName}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {FILTER_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            style={{
              fontSize: 11, padding: "5px 14px", borderRadius: 99, fontWeight: 600,
              background: filter === tab.key ? "rgba(97,0,255,0.35)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${filter === tab.key ? "rgba(97,0,255,0.55)" : "rgba(255,255,255,0.1)"}`,
              color: filter === tab.key ? "#a78bfa" : "#6b7280",
              cursor: "pointer", transition: "all 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Log entries */}
      <section>
        {isLoading ? (
          <div className="flex flex-col items-center gap-3" style={{ padding: "48px 0" }}>
            <div
              style={{
                width: 32, height: 32, borderRadius: "50%",
                border: "3px solid rgba(97,0,255,0.2)",
                borderTopColor: "#6100ff",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <p style={{ fontSize: 11, color: "#6b7280" }}>Loading trail…</p>
          </div>
        ) : isError ? (
          <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "32px 0" }}>
            Could not load trail. Check your connection and try again.
          </p>
        ) : entries.length === 0 ? (
          <p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "32px 0" }}>
            No entries yet. Complete or cancel tracks to build your trail.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {entries.map(entry => (
              <LogEntryCard
                key={entry.id}
                entry={entry}
                trailNotes={trailNotes}
                cancelReasons={cancelReasons}
                onNotesChanged={setTrailNotes}
              />
            ))}
          </div>
        )}
      </section>

      {/* Weekly Clip Rate */}
      <section
        className="rounded-xl border border-goat-border"
        style={{ background: "rgba(13,13,26,0.7)", padding: "16px 18px" }}
      >
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 10 }}>
          ▸ Clip Rate — Last 4 Weeks
        </p>
        {WEEK_LABELS.map((label, i) => (
          <div key={i} className="flex items-center gap-3 py-0.5">
            <span style={{ fontSize: 10, color: "#6b7280", width: 50, flexShrink: 0 }}>{label}</span>
            <ClipBar pct={weeklyRates[i] ?? null} />
          </div>
        ))}
      </section>

      {/* Achievements */}
      <section
        className="rounded-xl border border-goat-border"
        style={{ background: "rgba(13,13,26,0.7)", padding: "16px 18px" }}
      >
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 16 }}>
          ▸ Achievements
        </p>
        {[1, 2, 3].map(tier => {
          const tierAchievements = ACHIEVEMENTS.filter(a => a.tier === tier);
          return (
            <div key={tier} style={{ marginBottom: 20 }}>
              <p style={{ fontSize: 8, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 8, fontWeight: 700 }}>
                {TIER_LABELS[tier]}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {tierAchievements.map(a => {
                  const autoUnlocked =
                    (a.id === "first_blood"          && (player?.tasks_completed ?? 0) >= 1)  ||
                    (a.id === "the_grind"             && (player?.gait_streak ?? 0) >= 7)      ||
                    (a.id === "iron_commitment"       && (player?.stake_streak ?? 0) >= 14)    ||
                    (a.id === "fresh_cheese_factory"  && (player?.fresh_cheese ?? 0) >= 10);
                  const unlocked = autoUnlocked || unlockedAchievements.includes(a.id);
                  return (
                    <div
                      key={a.id}
                      className="rounded-lg"
                      style={{
                        padding: "10px 12px",
                        background: unlocked ? "rgba(97,0,255,0.12)" : "rgba(255,255,255,0.02)",
                        border: `1px solid ${unlocked ? "rgba(97,0,255,0.35)" : "rgba(255,255,255,0.06)"}`,
                        opacity: unlocked ? 1 : 0.45,
                      }}
                    >
                      <p style={{ fontSize: 16, marginBottom: 4 }}>{unlocked ? "🏆" : "🔒"}</p>
                      <p style={{ fontSize: 11, color: unlocked ? "#a78bfa" : "#6b7280", fontWeight: 700, marginBottom: 2, lineHeight: 1.3 }}>
                        {a.name}
                      </p>
                      <p style={{ fontSize: 9, color: "#6b7280", lineHeight: 1.4, marginBottom: 3 }}>{a.desc}</p>
                      <p style={{ fontSize: 8, color: "#4b5563", fontStyle: "italic" }}>{a.hint}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
