"use client";

import { useState, useEffect, useRef } from "react";

const AUTO_DISMISS_MS = 30_000;

function getQuestion(daysElapsed: number): string {
  if (daysElapsed <= 1)  return "What made this one flow? Worth noting for next time. 🐐";
  if (daysElapsed <= 5)  return "What finally got this one moving?";
  if (daysElapsed <= 14) return "This one sat for a while. What was the hold-up?";
  return "This took some time. What would have helped move it faster?";
}

interface TrailNotePromptProps {
  taskName: string;
  logId: number;
  daysElapsed: number;
  onDismiss: () => void;
}

export function TrailNotePrompt({ taskName, logId, daysElapsed, onDismiss }: TrailNotePromptProps) {
  const [note, setNote] = useState("");
  const [interacted, setInteracted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const question = getQuestion(daysElapsed);

  function resetTimer() {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(onDismiss, AUTO_DISMISS_MS);
  }

  useEffect(() => {
    resetTimer();
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleInteract() {
    if (!interacted) {
      setInteracted(true);
      if (timerRef.current) clearTimeout(timerRef.current);
    }
  }

  function handleSave() {
    const trimmed = note.trim();
    try {
      const existing = JSON.parse(localStorage.getItem("goatflow_trail_notes") || "{}");
      existing[String(logId)] = {
        question,
        note: trimmed,
        timestamp: Date.now(),
        taskName,
      };
      localStorage.setItem("goatflow_trail_notes", JSON.stringify(existing));
    } catch { /* ignore storage errors */ }
    onDismiss();
  }

  return (
    <div
      className="animate-gf-slide-up"
      style={{
        position: "fixed",
        bottom: 24,
        left: "50%",
        zIndex: 45,
        width: 400,
        maxWidth: "calc(100vw - 32px)",
      }}
      onMouseEnter={handleInteract}
      onTouchStart={handleInteract}
    >
      <div
        className="rounded-2xl border border-goat-border"
        style={{ background: "rgba(13,13,26,0.97)", padding: "18px 20px 16px", boxShadow: "0 8px 40px rgba(0,0,0,0.6)" }}
      >
        {/* Header */}
        <div className="flex items-start gap-2 mb-3">
          <span style={{ fontSize: 20, lineHeight: 1 }}>🐐</span>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 12, color: "#F5F5F5", fontWeight: 600, lineHeight: 1.4 }}>{question}</p>
            <p style={{ fontSize: 10, color: "#6b7280", marginTop: 2, fontStyle: "italic" }}>
              &ldquo;{taskName}&rdquo;
            </p>
          </div>
        </div>

        {/* Textarea */}
        <div style={{ position: "relative", marginBottom: 12 }}>
          <textarea
            value={note}
            onChange={e => { setNote(e.target.value.slice(0, 200)); handleInteract(); }}
            onFocus={handleInteract}
            placeholder="Optional — tap to add..."
            rows={3}
            style={{
              width: "100%", background: "rgba(97,0,255,0.07)", border: "1px solid rgba(97,0,255,0.25)",
              borderRadius: 10, padding: "9px 12px", fontSize: 12, color: "#F5F5F5",
              outline: "none", resize: "none", fontFamily: "inherit", boxSizing: "border-box",
            }}
          />
          <span style={{
            position: "absolute", bottom: 6, right: 10, fontSize: 9,
            color: note.length >= 180 ? "#ef4444" : "#4b5563",
          }}>
            {note.length}/200
          </span>
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 py-2 rounded-xl font-bold uppercase tracking-widest"
            style={{
              fontSize: 11, background: "rgba(97,0,255,0.35)", border: "1px solid rgba(97,0,255,0.55)",
              color: "#a78bfa", cursor: "pointer",
            }}
          >
            Save to Trail
          </button>
          <button
            onClick={onDismiss}
            style={{
              padding: "8px 16px", borderRadius: 10, fontSize: 11, color: "#6b7280",
              background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
              cursor: "pointer", whiteSpace: "nowrap",
            }}
          >
            Skip
          </button>
        </div>

        {/* Auto-dismiss hint */}
        {!interacted && (
          <p style={{ fontSize: 9, color: "#4b5563", textAlign: "center", marginTop: 8 }}>
            Auto-dismisses in {Math.ceil(AUTO_DISMISS_MS / 1000)}s — tap to keep open
          </p>
        )}
      </div>
    </div>
  );
}
