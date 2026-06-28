"use client";

import { usePlayer } from "@/lib/hooks/usePlayer";
import { pasture_name } from "@/lib/gamification";

export function LevelBar() {
  const { player } = usePlayer();

  const level        = player?.level ?? 1;
  const hayThisLevel = player?.hay_this_level ?? 0;
  const hayToNext    = player?.hay_to_next_level ?? 500;
  const pasture      = pasture_name(level);
  const pct = hayToNext > 0 ? Math.min(100, Math.round((hayThisLevel / hayToNext) * 100)) : 100;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 flex items-center px-4 gap-4"
      style={{
        height: 48,
        background: "rgba(13,13,26,0.95)",
        borderTop: "1px solid rgba(97,0,255,0.25)",
        backdropFilter: "blur(8px)",
      }}
    >
      {/* Left: pasture badge */}
      <div
        className="shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-full"
        style={{
          background: "linear-gradient(135deg, rgba(97,0,255,0.35), rgba(139,92,246,0.25))",
          border: "1px solid rgba(97,0,255,0.4)",
        }}
      >
        <span style={{ fontSize: 9, color: "#a78bfa", textTransform: "uppercase", letterSpacing: "0.12em", whiteSpace: "nowrap" }}>
          Lv {level} · {pasture}
        </span>
      </div>

      {/* Center: label + bar */}
      <div className="flex-1 flex flex-col justify-center gap-0.5 min-w-0">
        <div className="flex items-center justify-between" style={{ marginBottom: 2 }}>
          <span style={{ fontSize: 8, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.15em" }}>
            Pasture Gauge
          </span>
          <span style={{ fontSize: 8, color: "#9ca3af" }}>
            🌾 {(player?.hay ?? 0).toLocaleString()} Hay
          </span>
        </div>
        <div
          className="w-full rounded-full overflow-hidden"
          style={{ height: 6, background: "rgba(97,0,255,0.12)", border: "1px solid rgba(97,0,255,0.2)" }}
        >
          <div
            className="h-full rounded-full animate-metabolism-pulse"
            style={{
              width: `${pct}%`,
              background: "linear-gradient(90deg, #6100ff, #8B5CF6, #6100ff)",
              backgroundSize: "200% 100%",
              transition: "width 0.6s ease",
            }}
          />
        </div>
      </div>

      {/* Right: XP text */}
      <div className="shrink-0 text-right">
        <span style={{ fontSize: 10, color: "#a78bfa", fontWeight: 600, whiteSpace: "nowrap" }}>
          {hayThisLevel.toLocaleString()}
          <span style={{ color: "#6b7280" }}> / {hayToNext.toLocaleString()} Hay</span>
        </span>
      </div>
    </div>
  );
}
