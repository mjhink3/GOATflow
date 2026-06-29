"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getLeaderboard, type LeaderboardEntry } from "@/lib/api/leaderboard";

const TABS: { key: string; label: string; unit: string }[] = [
  { key: "hay",    label: "Lifetime Hay",  unit: "Hay"   },
  { key: "cheese", label: "Fresh Cheese",  unit: "🧀"    },
  { key: "tracks", label: "Tracks",        unit: "tracks" },
  { key: "gait",   label: "GAIT Streak",   unit: "days"  },
  { key: "stakes", label: "Stake Streak",  unit: "days"  },
];

const MEDALS = ["🥇", "🥈", "🥉"];

function RankCell({ rank }: { rank: number }) {
  if (rank <= 3) return <span style={{ fontSize: 18 }}>{MEDALS[rank - 1]}</span>;
  return <span style={{ fontSize: 12, color: "#6b7280", fontWeight: 600, width: 28, display: "inline-block", textAlign: "center" }}>#{rank}</span>;
}

function LeaderRow({ entry, unit }: { entry: LeaderboardEntry; unit: string }) {
  return (
    <div
      style={{
        display: "flex", alignItems: "center", gap: 12,
        padding: "10px 14px", borderRadius: 8,
        background: entry.is_current_user ? "rgba(97,0,255,0.08)" : "rgba(255,255,255,0.02)",
        borderLeft: entry.is_current_user ? "3px solid #7c3aed" : "3px solid transparent",
        marginBottom: 4,
      }}
    >
      <div style={{ width: 32, flexShrink: 0, display: "flex", justifyContent: "center" }}>
        <RankCell rank={entry.rank} />
      </div>
      <span style={{ flex: 1, fontSize: 13, color: entry.is_current_user ? "#a78bfa" : "#F5F5F5", fontWeight: entry.is_current_user ? 700 : 400 }}>
        {entry.display_name}{entry.is_current_user ? " (you)" : ""}
      </span>
      <span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>
        {entry.value.toLocaleString()} <span style={{ fontSize: 10, color: "#6b7280", fontWeight: 400 }}>{unit}</span>
      </span>
    </div>
  );
}

export default function LeaderboardPage() {
  const router = useRouter();
  const [category, setCategory] = useState("hay");
  const activeTab = TABS.find(t => t.key === category)!;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["leaderboard", category],
    queryFn: () => getLeaderboard(category),
    staleTime: 60_000,
  });

  const userInTop20 = data?.entries.some(e => e.is_current_user) ?? true;
  const currentRank = data?.current_user_rank;

  return (
    <div className="flex flex-col gap-6 px-5 py-6 pb-16 max-w-2xl mx-auto w-full pt-16 md:pt-6">

      {/* Back button */}
      <button
        onClick={() => router.push("/dashboard")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontSize: 11, color: "#6b7280", background: "none", border: "none",
          cursor: "pointer", padding: 0, alignSelf: "flex-start",
        }}
      >
        ← Back to Dashboard
      </button>

      {/* Header */}
      <div className="flex items-center gap-3">
        <span style={{ fontSize: 26 }}>🏆</span>
        <h1 className="font-syne font-bold text-goat-white" style={{ fontSize: 22 }}>The Herd Leaderboard</h1>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setCategory(tab.key)}
            style={{
              fontSize: 11, padding: "5px 14px", borderRadius: 99, fontWeight: 600, cursor: "pointer",
              background: category === tab.key ? "rgba(97,0,255,0.35)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${category === tab.key ? "rgba(97,0,255,0.55)" : "rgba(255,255,255,0.1)"}`,
              color: category === tab.key ? "#a78bfa" : "#6b7280",
              transition: "all 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Board */}
      <section className="rounded-xl border border-goat-border" style={{ background: "rgba(13,13,26,0.7)", padding: "16px" }}>
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>
          ▸ Top 20 — {activeTab.label}
        </p>

        {isLoading ? (
          <div className="flex flex-col items-center gap-3 py-10">
            <div style={{ width: 28, height: 28, borderRadius: "50%", border: "3px solid rgba(97,0,255,0.2)", borderTopColor: "#6100ff", animation: "spin 0.8s linear infinite" }} />
            <p style={{ fontSize: 11, color: "#6b7280" }}>Loading herd…</p>
          </div>
        ) : isError ? (
          <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "24px 0" }}>Failed to load leaderboard.</p>
        ) : !data || data.entries.length === 0 ? (
          <p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "24px 0" }}>No entries yet. Be the first GOAT.</p>
        ) : (
          <>
            {data.entries.map(entry => (
              <LeaderRow key={entry.user_id} entry={entry} unit={activeTab.unit} />
            ))}

            {!userInTop20 && currentRank && (
              <>
                <div style={{ borderTop: "1px solid #2A2A4A", margin: "12px 0 8px" }} />
                <div
                  style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "10px 14px", borderRadius: 8,
                    background: "rgba(97,0,255,0.08)", borderLeft: "3px solid #7c3aed",
                  }}
                >
                  <div style={{ width: 32, flexShrink: 0, textAlign: "center" }}>
                    <span style={{ fontSize: 12, color: "#a78bfa", fontWeight: 700 }}>#{currentRank}</span>
                  </div>
                  <span style={{ flex: 1, fontSize: 13, color: "#a78bfa", fontWeight: 700 }}>You</span>
                </div>
              </>
            )}
          </>
        )}
      </section>
    </div>
  );
}
