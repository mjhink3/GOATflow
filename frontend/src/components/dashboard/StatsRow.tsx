"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useSignals } from "@/lib/hooks/useSignals";
import { usePlayer } from "@/lib/hooks/usePlayer";
import { useHorns } from "@/lib/hooks/useHorns";
import { GF_QUOTES } from "@/lib/gamification";

interface StatCardProps {
  icon: string;
  value: string | number;
  label: string;
  sub?: string;
  color?: string;
}

function StatCard({ icon, value, label, sub, color = "#F5F5F5" }: StatCardProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-1 p-4 rounded-xl border border-goat-border"
      style={{ background: "rgba(26,26,46,0.6)", minHeight: 120 }}
    >
      <Image src={icon} alt={label} width={56} height={56} />
      <span style={{ fontSize: 24, fontWeight: 800, color, lineHeight: 1, fontFamily: "var(--font-syne)", textAlign: "center", marginBottom: 4 }}>
        {value}
      </span>
      <span style={{ fontSize: 11, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.1em", textAlign: "center" }}>
        {label}
      </span>
      {sub && <span style={{ fontSize: 10, color: "#6b7280", textAlign: "center" }}>{sub}</span>}
    </div>
  );
}

interface PrecisionStats { precise: number; total: number }

export function StatsRow() {
  const { signals } = useSignals();
  const { player } = usePlayer();
  const { horns } = useHorns();
  const [quote, setQuote] = useState("");
  const [precision, setPrecision] = useState<PrecisionStats | null>(null);

  useEffect(() => {
    setQuote(GF_QUOTES[Math.floor(Math.random() * GF_QUOTES.length)]);
    const raw = localStorage.getItem("goatflow_precision_stats");
    if (raw) {
      try { setPrecision(JSON.parse(raw) as PrecisionStats); } catch { /* ignore */ }
    }
  }, []);

  const activeTracks = signals.length;
  const summitCalls  = signals.filter(s => s.bleat_type === "Summit Call").length;

  const clipPct    = player?.weekly_clip_rate != null ? Math.round(player.weekly_clip_rate * 100) : null;
  const clipColor  = clipPct === null ? "#9ca3af" : clipPct >= 75 ? "#53c660" : clipPct >= 50 ? "#f59e0b" : "#ef4444";
  const clipDisplay = clipPct !== null ? `${clipPct}%` : "—";

  // Stakes % — honor rate (claimed vs broken) over last 30 days
  const stakesPct   = player?.stakes_honor_rate ?? null;
  const stakesValue = stakesPct != null ? `${Math.round(stakesPct)}%` : "—";
  const stakesColor = stakesPct == null ? "#9ca3af" : stakesPct >= 80 ? "#53c660" : stakesPct >= 60 ? "#f59e0b" : "#ef4444";
  const stakesSub   = stakesPct == null ? "Need 3+ stakes" : "30d honor rate";

  // Precision (localStorage)
  const precisionUnlocked = precision !== null && precision.total >= 5;
  const precisionPct   = precisionUnlocked ? Math.round(precision!.precise / precision!.total * 100) : null;
  const precisionValue = precisionPct !== null ? `${precisionPct}%` : "—";
  const precisionSub   = precision === null
    ? "Track timed tasks"
    : precision.total < 5
    ? `${precision.total}/5 to unlock`
    : `${precision.precise}/${precision.total} on time`;
  const precisionColor = precisionPct === null ? "#9ca3af" : precisionPct >= 80 ? "#53c660" : precisionPct >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col gap-3 mb-4">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        <StatCard icon="/icons/icon_tracks.webp"        value={activeTracks}                          label="Active Tracks" />
        <StatCard icon="/icons/icon_summit.webp"         value={summitCalls}                           label="Summit Calls"  color="#ef4444" />
        <StatCard icon="/icons/icon_completed.webp"      value={player?.tasks_completed ?? 0}           label="Completed"     sub="lifetime" />
        <StatCard icon="/icons/icon_hay_stack.webp"      value={(player?.hay ?? 0).toLocaleString()}   label="Hay Balance"   color="#f59e0b" />
        <StatCard icon="/icons/icon_fresh_cheese.webp"   value={player?.fresh_cheese ?? 0}              label="Fresh Cheese"  color="#53c660" />
        <StatCard icon="/icons/icon_horns.webp"          value={horns.length}                           label="Active Horns"  sub="/ 10 max" />
        <StatCard icon="/icons/icon_clip_rate.webp"      value={clipDisplay}                            label="Clip Rate"     sub="7 day"   color={clipColor} />
        <StatCard icon="/icons/icon_gait.webp"           value={`${player?.gait_streak ?? 0}d`}        label="GAIT Streak"   sub={`🛡️ ${player?.streak_shields ?? 0} shields banked`} color="#8B5CF6" />
        <StatCard icon="/icons/icon_stakes.png"          value={stakesValue}                            label="Stakes %"      sub={stakesSub} color={stakesColor} />
        <StatCard icon="/icons/icon_precision.png"       value={precisionValue}                         label="Precision"     sub={precisionSub} color={precisionColor} />
      </div>

      {/* Daily quote */}
      {quote && (
        <div
          className="px-4 py-3 rounded-xl border border-goat-border animate-gf-fade-in"
          style={{ background: "rgba(97,0,255,0.06)" }}
        >
          <p style={{ fontSize: 11, color: "#9ca3af", fontStyle: "italic", lineHeight: 1.6 }}>
            &ldquo;{quote}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}
