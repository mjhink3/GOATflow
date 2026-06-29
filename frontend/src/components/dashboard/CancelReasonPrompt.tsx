"use client";

import { useState, useEffect, useRef } from "react";
import { saveCancelReason } from "@/lib/api/behavioral";

interface Props {
  taskName: string;
  logId: number | null;
  onDone: () => void;
}

export function CancelReasonPrompt({ taskName, logId, onDone }: Props) {
  const [reason, setReason] = useState("");
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const QUICK = ["Added by mistake", "Already completed", "No longer relevant", "Didn't have time"];

  useEffect(() => {
    timerRef.current = setTimeout(onDone, 20000);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [onDone]);

  function pause() { if (timerRef.current) clearTimeout(timerRef.current); }

  function save() {
    if (logId) {
      const store = JSON.parse(localStorage.getItem("goatflow_cancel_reasons") || "{}");
      store[String(logId)] = { reason: reason.trim(), taskName, timestamp: Date.now() };
      localStorage.setItem("goatflow_cancel_reasons", JSON.stringify(store));
    }
    saveCancelReason({ log_id: logId ?? undefined, task_name: taskName, reason: reason.trim() || undefined });
    setSaved(true);
    setTimeout(onDone, 800);
  }

  return (
    <div
      className="animate-gf-slide-up"
      style={{
        position: "fixed", bottom: 80, left: "50%", transform: "translateX(-50%)",
        width: "90%", maxWidth: 400, zIndex: 9999,
        background: "rgba(8,8,15,0.97)", border: "1px solid rgba(239,68,68,0.2)",
        borderRadius: 10, padding: "12px 16px",
      }}
      onMouseEnter={pause} onTouchStart={pause}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 16, flexShrink: 0 }}>🐐</span>
        <span style={{ fontSize: 12, color: "#9ca3af", fontFamily: "var(--font-dm-sans)", lineHeight: 1.5 }}>
          Why did <strong style={{ color: "#F5F5F5" }}>{taskName}</strong> get cancelled? <span style={{ color: "#4b5563" }}>(optional)</span>
        </span>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
        {QUICK.map(q => (
          <button key={q} onClick={() => { pause(); setReason(q); }}
            style={{
              fontSize: 10, padding: "4px 10px", borderRadius: 20, cursor: "pointer",
              background: reason === q ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.05)",
              border: `1px solid ${reason === q ? "rgba(239,68,68,0.5)" : "rgba(255,255,255,0.1)"}`,
              color: reason === q ? "#fca5a5" : "#6b7280",
            }}
          >{q}</button>
        ))}
      </div>

      <input
        value={reason}
        onChange={e => { pause(); setReason(e.target.value); }}
        placeholder="Or type your own reason…"
        maxLength={120}
        style={{
          width: "100%", background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6,
          padding: "7px 10px", fontSize: 12, color: "#e5e7eb",
          outline: "none", marginBottom: 10, boxSizing: "border-box",
          fontFamily: "var(--font-dm-sans)",
        }}
      />

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
        <button onClick={onDone} style={{ background: "none", border: "none", color: "#4b5563", fontSize: 11, cursor: "pointer" }}>Skip</button>
        <button onClick={save} style={{ background: "none", border: "none", color: saved ? "#53c660" : "#a78bfa", fontSize: 11, fontWeight: 500, cursor: "pointer" }}>
          {saved ? "Saved ✓" : "Save Reason"}
        </button>
      </div>
    </div>
  );
}
