"use client";

import { useState, useEffect, useRef } from "react";
import { saveGutCheck } from "@/lib/api/behavioral";

const AUTO_DISMISS_MS = 15_000;

const RATINGS = [
  { key: "correct",  label: "👍 Nailed it" },
  { key: "too_low",  label: "⬆️ Too low" },
  { key: "too_high", label: "⬇️ Too high" },
] as const;

type RatingKey = typeof RATINGS[number]["key"];

interface TrackRatingPromptProps {
  taskName: string;
  tier: string;
  logId: number;
  onDismiss: () => void;
}

export function TrackRatingPrompt({ taskName, tier, logId, onDismiss }: TrackRatingPromptProps) {
  const [rating, setRating] = useState<RatingKey | null>(null);
  const [reason, setReason] = useState("");
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dismissRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    timerRef.current = setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (dismissRef.current) clearTimeout(dismissRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSave() {
    try {
      const existing = JSON.parse(localStorage.getItem("goatflow_track_ratings") || "[]");
      existing.push({ log_id: logId, task_name: taskName, tier, rating, reason: reason.trim(), timestamp: Date.now() });
      localStorage.setItem("goatflow_track_ratings", JSON.stringify(existing));
    } catch { /* ignore */ }
    if (rating) {
      saveGutCheck({ log_id: logId, task_name: taskName, assigned_tier: tier, rating, reason: reason.trim() || undefined });
    }
    if (timerRef.current) clearTimeout(timerRef.current);
    setSaved(true);
    dismissRef.current = setTimeout(onDismiss, 1000);
  }

  return (
    <div
      className="animate-gf-slide-up"
      style={{ position: "fixed", bottom: 24, left: "50%", zIndex: 45, width: 400, maxWidth: "calc(100vw - 32px)" }}
    >
      <div
        className="rounded-2xl border border-goat-border"
        style={{ background: "rgba(13,13,26,0.97)", padding: "18px 20px 16px", boxShadow: "0 8px 40px rgba(0,0,0,0.6)" }}
      >
        {saved ? (
          <p style={{ fontSize: 13, color: "#53c660", textAlign: "center", padding: "8px 0" }}>
            Got it. Making the goat smarter. 🐐
          </p>
        ) : (
          <>
            <div className="flex items-start gap-2 mb-3">
              <span style={{ fontSize: 20, lineHeight: 1 }}>🐐</span>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 12, color: "#F5F5F5", fontWeight: 600, lineHeight: 1.4 }}>Quick gut check 🐐</p>
                <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>Did GOATflow rank this one right?</p>
                <p style={{ fontSize: 10, color: "#6b7280", marginTop: 4, fontStyle: "italic" }}>
                  &ldquo;{taskName}&rdquo; &mdash; <span style={{ color: "#a78bfa" }}>{tier}</span>
                </p>
              </div>
            </div>

            <div className="flex gap-2 mb-3">
              {RATINGS.map(r => (
                <button
                  key={r.key}
                  onClick={() => setRating(r.key)}
                  style={{
                    flex: 1, padding: "8px 4px", borderRadius: 8, fontSize: 11, cursor: "pointer",
                    background: rating === r.key ? "rgba(97,0,255,0.35)" : "rgba(255,255,255,0.04)",
                    border: `1px solid ${rating === r.key ? "rgba(97,0,255,0.55)" : "rgba(255,255,255,0.1)"}`,
                    color: rating === r.key ? "#a78bfa" : "#9ca3af",
                    transition: "all 0.15s",
                  }}
                >
                  {r.label}
                </button>
              ))}
            </div>

            <input
              value={reason}
              onChange={e => setReason(e.target.value.slice(0, 100))}
              placeholder="Why do you think so? (optional)"
              style={{
                width: "100%", background: "rgba(97,0,255,0.07)", border: "1px solid rgba(97,0,255,0.25)",
                borderRadius: 8, padding: "7px 10px", fontSize: 11, color: "#F5F5F5",
                outline: "none", fontFamily: "inherit", marginBottom: 10, boxSizing: "border-box",
              }}
            />

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={!rating}
                className="flex-1 py-2 rounded-xl font-bold uppercase tracking-widest"
                style={{
                  fontSize: 11,
                  background: rating ? "rgba(97,0,255,0.35)" : "rgba(97,0,255,0.1)",
                  border: `1px solid ${rating ? "rgba(97,0,255,0.55)" : "rgba(97,0,255,0.2)"}`,
                  color: rating ? "#a78bfa" : "#6b7280",
                  cursor: rating ? "pointer" : "not-allowed",
                }}
              >
                Submit
              </button>
              <button
                onClick={onDismiss}
                style={{
                  padding: "8px 16px", borderRadius: 10, fontSize: 11, color: "#6b7280",
                  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                  cursor: "pointer",
                }}
              >
                Skip
              </button>
            </div>

            <p style={{ fontSize: 9, color: "#4b5563", textAlign: "center", marginTop: 8 }}>
              Auto-dismisses in {Math.ceil(AUTO_DISMISS_MS / 1000)}s
            </p>
          </>
        )}
      </div>
    </div>
  );
}
