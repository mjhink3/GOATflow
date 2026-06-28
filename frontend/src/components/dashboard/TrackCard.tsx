"use client";

import { useState } from "react";
import Image from "next/image";
import type { Signal, CompletionResult } from "@/lib/types";

interface CancelResult { ok: boolean; log_id: number | null; task_name: string; }

interface TrackCardProps {
  signal: Signal;
  index: number;
  onComplete: (id: number) => Promise<CompletionResult>;
  onCancel: (id: number) => Promise<CancelResult>;
  onCompleted: (result: CompletionResult) => void;
  onCancelled?: (taskName: string, logId: number | null) => void;
}

const TIER_STYLES: Record<string, { bg: string; border: string; color: string; label: string }> = {
  Micro: {
    bg: "rgba(83,198,96,0.12)", border: "rgba(83,198,96,0.35)", color: "#53c660", label: "Micro",
  },
  Standard: {
    bg: "rgba(97,0,255,0.12)", border: "rgba(97,0,255,0.35)", color: "#a78bfa", label: "Standard",
  },
  "High-Leverage": {
    bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.4)", color: "#f59e0b", label: "High-Leverage",
  },
  GOAT: {
    bg: "linear-gradient(135deg,rgba(139,92,246,0.18),rgba(97,0,255,0.12))",
    border: "rgba(139,92,246,0.4)", color: "#c4b5fd", label: "GOAT",
  },
};

export function TrackCard({ signal, index, onComplete, onCancel, onCompleted, onCancelled }: TrackCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState<"complete" | "cancel" | null>(null);

  const isSummit = signal.bleat_type === "Summit Call";
  const isHighLev = signal.xp_reward === "High-Leverage";
  const tier = TIER_STYLES[signal.xp_reward] ?? TIER_STYLES.Standard;

  const leftBorder = isSummit
    ? "4px solid #ef4444"
    : isHighLev
    ? "4px solid #f59e0b"
    : "4px solid rgba(97,0,255,0.5)";

  const cardGlow = isHighLev
    ? "0 0 12px rgba(245,158,11,0.18)"
    : isSummit
    ? "0 0 10px rgba(239,68,68,0.12)"
    : "none";

  async function handleComplete() {
    setLoading("complete");
    try {
      const result = await onComplete(signal.id);
      onCompleted(result);
    } catch (err) {
      console.error("[TrackCard] complete failed:", err);
    } finally {
      setLoading(null);
    }
  }

  async function handleCancel() {
    if (!confirming) { setConfirming(true); return; }
    setLoading("cancel");
    try {
      const result = await onCancel(signal.id);
      onCancelled?.(result.task_name, result.log_id);
    } catch (err) {
      console.error("[TrackCard] cancel failed:", err);
      window.alert("Failed to cancel track. Try again.");
    } finally {
      setLoading(null);
      setConfirming(false);
    }
  }

  return (
    <div
      className="relative rounded-xl border border-goat-border animate-track-slide-up overflow-hidden"
      style={{
        background: "rgba(26,26,46,0.7)",
        borderLeft: leftBorder,
        boxShadow: cardGlow,
        animationDelay: `${index * 60}ms`,
        padding: "14px 14px 12px 14px",
      }}
    >
      {/* Faded weight number */}
      <span
        style={{
          position: "absolute", top: 10, right: 12,
          fontSize: 42, fontWeight: 800, color: "rgba(97,0,255,0.3)",
          fontFamily: "var(--font-syne)", lineHeight: 1, pointerEvents: "none",
          userSelect: "none",
        }}
      >
        {signal.operational_weight.toFixed(0)}
      </span>

      {/* Task name */}
      <p
        className="font-syne text-goat-white font-bold leading-snug pr-10"
        style={{ fontSize: 14, marginBottom: 4 }}
      >
        {signal.task_name}
      </p>

      {/* Why */}
      <p style={{ fontSize: 11, color: "#9ca3af", lineHeight: 1.5, marginBottom: 8 }}>
        {signal.why}
      </p>

      {/* Horn attribution */}
      {signal.directive_applied && signal.horn_applied_name && (
        <p style={{ fontSize: 10, color: "#a78bfa", fontStyle: "italic", marginBottom: 6 }}>
          ◆ Directed by: {signal.horn_applied_name}
        </p>
      )}

      {/* Tags row */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        {/* Bleat type */}
        {isSummit ? (
          <span style={{
            fontSize: 9, padding: "2px 8px", borderRadius: 99, fontWeight: 700, textTransform: "uppercase",
            background: "linear-gradient(135deg,rgba(255,59,59,0.25),rgba(255,100,0,0.15))",
            border: "1px solid rgba(239,68,68,0.5)", color: "#ef4444", letterSpacing: "0.1em",
          }}>
            🚨 Summit Call
          </span>
        ) : (
          <span style={{
            fontSize: 9, padding: "2px 8px", borderRadius: 99, textTransform: "uppercase",
            background: "rgba(83,198,96,0.08)", border: "1px solid rgba(83,198,96,0.25)",
            color: "#53c660", letterSpacing: "0.1em",
          }}>
            Routine Grazing
          </span>
        )}

        {/* Tier badge */}
        <span style={{
          fontSize: 9, padding: "2px 8px", borderRadius: 99, textTransform: "uppercase",
          background: tier.bg, border: `1px solid ${tier.border}`, color: tier.color, letterSpacing: "0.1em",
        }}>
          {tier.label}
        </span>

        {/* Category */}
        {signal.category && signal.category !== "other" && (
          <span style={{
            fontSize: 9, padding: "2px 6px", borderRadius: 99,
            background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.2)",
            color: "#7c3aed", textTransform: "uppercase", letterSpacing: "0.08em",
          }}>
            {signal.category}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleComplete}
          disabled={loading !== null}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50"
          style={{
            fontSize: 11, background: "rgba(97,0,255,0.22)", border: "1px solid rgba(97,0,255,0.45)",
            color: "#a78bfa", cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          <Image src="/icons/icon_completed.webp" alt="" width={13} height={13} />
          {loading === "complete" ? "Marking…" : "Complete?"}
        </button>

        <button
          onClick={handleCancel}
          disabled={loading !== null}
          className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
          style={{
            fontSize: 11,
            background: confirming ? "rgba(239,68,68,0.2)" : "rgba(239,68,68,0.08)",
            border: confirming ? "1px solid rgba(239,68,68,0.6)" : "1px solid rgba(239,68,68,0.25)",
            color: "#ef4444", cursor: loading ? "not-allowed" : "pointer", whiteSpace: "nowrap",
          }}
        >
          <Image src="/icons/icon_cancel.webp" alt="" width={13} height={13} />
          {loading === "cancel" ? "Cancelling…" : confirming ? "Confirm?" : "Cancel"}
        </button>
      </div>

      {confirming && (
        <button
          onClick={() => setConfirming(false)}
          style={{ fontSize: 9, color: "#6b7280", marginTop: 4, background: "none", border: "none", cursor: "pointer" }}
        >
          ← Never mind
        </button>
      )}
    </div>
  );
}
