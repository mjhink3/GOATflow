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

  const freshnessPct  = player?.freshness_pct ?? 100;
  const cheeseState   = player?.cheese_state ?? "fresh";
  const hoursSince    = player?.hours_since_completion ?? null;

  const freshnessBarColor =
    freshnessPct > 75 ? "#53c660"
    : freshnessPct > 50 ? "#84cc16"
    : freshnessPct > 25 ? "#f59e0b"
    : freshnessPct > 0  ? "#f97316"
    : "#ef4444";

  const pillLabel =
    cheeseState === "rotting" ? "🚨 Rotting"
    : cheeseState === "staling" ? "⚠️ Staling"
    : freshnessPct <= 25 ? "⚠️ Soon"
    : "🧀 Fresh";

  const pillColor =
    cheeseState === "rotting" ? "#f87171"
    : (cheeseState === "staling" || freshnessPct <= 25) ? "#f59e0b"
    : "#53c660";

  const pillBg =
    cheeseState === "rotting" ? "rgba(239,68,68,0.15)"
    : (cheeseState === "staling" || freshnessPct <= 25) ? "rgba(245,158,11,0.15)"
    : "rgba(83,198,96,0.12)";

  const timeAgo =
    hoursSince === null
      ? null
      : hoursSince < 1
      ? "Last: <1h ago"
      : `Last: ${hoursSince}h ago`;

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

      {/* Center: label + hay bar + freshness bar */}
      <div className="flex-1 flex flex-col justify-center gap-0.5 min-w-0">
        <div className="flex items-center justify-between" style={{ marginBottom: 2 }}>
          <span style={{ fontSize: 8, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.15em" }}>
            Pasture Gauge
          </span>
          {/* Freshness status pill */}
          <span style={{
            fontSize: 8, padding: "1px 6px", borderRadius: 99,
            background: pillBg, color: pillColor,
            border: `1px solid ${pillColor}44`,
            whiteSpace: "nowrap",
          }}>
            {pillLabel}
          </span>
        </div>

        {/* Hay progress bar */}
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

        {/* Freshness bar */}
        <div
          className="w-full rounded-full overflow-hidden"
          style={{ height: 3, background: "rgba(255,255,255,0.06)", marginTop: 2 }}
        >
          <div
            style={{
              height: "100%",
              width: `${freshnessPct}%`,
              background: freshnessBarColor,
              borderRadius: 99,
              transition: "width 0.6s ease",
            }}
          />
        </div>
      </div>

      {/* Right: hay XP + time since last track */}
      <div className="shrink-0 flex flex-col items-end gap-0.5">
        <span style={{ fontSize: 10, color: "#a78bfa", fontWeight: 600, whiteSpace: "nowrap" }}>
          {hayThisLevel.toLocaleString()}
          <span style={{ color: "#6b7280" }}> / {hayToNext.toLocaleString()} Hay</span>
        </span>
        {player && (
          <span style={{ fontSize: 8, color: "#4b5563", whiteSpace: "nowrap" }}>
            {timeAgo ?? "No tracks yet"}
          </span>
        )}
      </div>
    </div>
  );
}
