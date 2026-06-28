"use client";

import Image from "next/image";
import { usePlayer } from "@/lib/hooks/usePlayer";
import { ascension_rank, pasture_name } from "@/lib/gamification";

const LEVEL_IMAGES: Record<number, string> = {
  1: "/assets/GOATflow_The_Kid_level_1_1773616494954.webp",
  2: "/assets/GOATflow_The_Starter_level_2_1773616494956.webp",
  3: "/assets/GOATflow_The_Builder_level_3_1773616494949.webp",
  4: "/assets/WorkGOAT_The_Climber_level_4_1773616494957.webp",
  5: "/assets/GOATflow_The_Leader_level_5_1773616494955.webp",
  6: "/assets/GOATflow_The_Visionary_level_6_1773616494957.webp",
  7: "/assets/GOATflow_The_G.O.A.T._level_7_1773616494953.webp",
};

export function RankCard() {
  const { player } = usePlayer();
  const level = player?.level ?? 1;
  const rank = ascension_rank(level);
  const pasture = pasture_name(level);
  const levelImg = LEVEL_IMAGES[Math.min(level, 7)] ?? LEVEL_IMAGES[7];

  const shareText = `I'm "${rank}" on GOATflow — Level ${level} · ${pasture} 🐐\n\n${player?.tasks_completed ?? 0} tracks completed · ${player?.gait_streak ?? 0}d GAIT streak · ${player?.fresh_cheese ?? 0} Fresh Cheese banked\n\n#GOATflow #productivity`;
  const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?text=${encodeURIComponent(shareText)}`;

  return (
    <div className="flex flex-col gap-3">
      {/* The card itself */}
      <div
        style={{
          background: "#08080f",
          border: "1px solid #2A2A4A",
          borderRadius: 12,
          padding: "20px 24px",
          display: "flex",
          gap: 20,
          alignItems: "center",
        }}
      >
        {/* Level avatar */}
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            flexShrink: 0,
            backgroundImage: `url(${levelImg})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            border: "2px solid #7c3aed",
          }}
        />

        {/* Info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <Image src="/icons/goatflow_logo_nobg.webp" alt="" width={20} height={20} style={{ borderRadius: 3 }} />
            <span style={{ fontSize: 9, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.12em" }}>GOATflow</span>
          </div>
          <p style={{ fontSize: 20, fontFamily: "var(--font-syne)", fontWeight: 800, color: "#F5F5F5", lineHeight: 1.1, marginBottom: 2 }}>
            {rank}
          </p>
          <p style={{ fontSize: 11, color: "#a78bfa", marginBottom: 12 }}>Lv {level} · {pasture}</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "3px 16px" }}>
            <span style={{ fontSize: 10, color: "#9ca3af" }}>🌾 {(player?.total_hay_earned ?? 0).toLocaleString()} Hay</span>
            <span style={{ fontSize: 10, color: "#9ca3af" }}>✅ {player?.tasks_completed ?? 0} completed</span>
            <span style={{ fontSize: 10, color: "#9ca3af" }}>🔥 {player?.gait_streak ?? 0}d streak</span>
            <span style={{ fontSize: 10, color: "#9ca3af" }}>🧀 {player?.fresh_cheese ?? 0} cheese</span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <a
          href={linkedInUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            padding: "8px 14px", borderRadius: 8, fontSize: 11, fontWeight: 600,
            background: "rgba(0,119,181,0.12)", border: "1px solid rgba(0,119,181,0.35)",
            color: "#38bdf8", textDecoration: "none", cursor: "pointer",
          }}
        >
          🔗 Share on LinkedIn
        </a>
        <button
          onClick={() => {
            const text = `${rank} | Lv ${level} · ${pasture}\n${player?.tasks_completed ?? 0} completed · ${player?.gait_streak ?? 0}d GAIT streak\ngoa tflow.com`;
            navigator.clipboard.writeText(text).then(() => alert("Rank copied to clipboard!")).catch(() => {});
          }}
          style={{
            padding: "8px 14px", borderRadius: 8, fontSize: 11, fontWeight: 600,
            background: "rgba(97,0,255,0.12)", border: "1px solid rgba(97,0,255,0.3)",
            color: "#a78bfa", cursor: "pointer",
          }}
        >
          Copy Stats
        </button>
      </div>
    </div>
  );
}
