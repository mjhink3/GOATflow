"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { usePlayer } from "@/lib/hooks/usePlayer";
import {
  getLeaderboard,
  getWeeklyMovers,
  getHeatCheck,
  type LeaderboardEntry,
} from "@/lib/api/leaderboard";

const TABS = [
  { key: "top_goats",     label: "🐐 Top Goats" },
  { key: "weekly_movers", label: "📈 Weekly Movers" },
  { key: "streaks",       label: "🔥 Streaks" },
  { key: "heat_check",    label: "🌡️ Pasture Heat Check" },
  { key: "my_climb",      label: "🧗 My Climb" },
];

const MEDALS = ["🥇", "🥈", "🥉"];

function streakTierLabel(days: number): string {
  if (days >= 30) return "Unshorn Legend 🏔️";
  if (days >= 14) return "Herd Locked 🔒";
  if (days >= 7)  return "On Traaack 🐐";
  if (days >= 3)  return "Warming Up 🌱";
  return "";
}

function flameCount(days: number): string {
  return "🔥".repeat(Math.min(5, Math.max(1, Math.ceil(days / 6))));
}

function RankCell({ rank }: { rank: number }) {
  if (rank <= 3) return <span style={{ fontSize: 18 }}>{MEDALS[rank - 1]}</span>;
  return (
    <span style={{ fontSize: 12, color: "#6b7280", fontWeight: 600, width: 28, display: "inline-block", textAlign: "center" }}>
      #{rank}
    </span>
  );
}

function LeaderRow({ entry, valueDisplay, valueSub }: {
  entry: LeaderboardEntry;
  valueDisplay: React.ReactNode;
  valueSub?: React.ReactNode;
}) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12,
      padding: "10px 14px", borderRadius: 8, marginBottom: 4,
      background: entry.is_current_user ? "rgba(97,0,255,0.08)" : "rgba(255,255,255,0.02)",
      borderLeft: entry.is_current_user ? "3px solid #7c3aed" : "3px solid transparent",
    }}>
      <div style={{ width: 32, flexShrink: 0, display: "flex", justifyContent: "center" }}>
        <RankCell rank={entry.rank} />
      </div>
      <span style={{ flex: 1, fontSize: 13, color: entry.is_current_user ? "#a78bfa" : "#F5F5F5", fontWeight: entry.is_current_user ? 700 : 400 }}>
        {entry.display_name}{entry.is_current_user ? " (you)" : ""}
      </span>
      <div style={{ textAlign: "right" }}>
        {valueDisplay}
        {valueSub && <div style={{ marginTop: 2 }}>{valueSub}</div>}
      </div>
    </div>
  );
}

function BoardSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-goat-border" style={{ background: "rgba(13,13,26,0.7)", padding: "16px" }}>
      <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>
        ▸ {label}
      </p>
      {children}
    </section>
  );
}

function UserFooter({ rank }: { rank: number }) {
  return (
    <>
      <div style={{ borderTop: "1px solid #2A2A4A", margin: "12px 0 8px" }} />
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        padding: "10px 14px", borderRadius: 8,
        background: "rgba(97,0,255,0.08)", borderLeft: "3px solid #7c3aed",
      }}>
        <div style={{ width: 32, textAlign: "center" }}>
          <span style={{ fontSize: 12, color: "#a78bfa", fontWeight: 700 }}>#{rank}</span>
        </div>
        <span style={{ fontSize: 13, color: "#a78bfa", fontWeight: 700 }}>You</span>
      </div>
    </>
  );
}

function StatTile({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl p-3 border border-goat-border" style={{ background: "rgba(26,26,46,0.6)" }}>
      <p style={{ fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>{label}</p>
      <p style={{ fontSize: 20, fontWeight: 800, color, fontFamily: "var(--font-syne)" }}>{value}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center gap-3 py-10">
      <div style={{ width: 28, height: 28, borderRadius: "50%", border: "3px solid rgba(97,0,255,0.2)", borderTopColor: "#6100ff", animation: "spin 0.8s linear infinite" }} />
      <p style={{ fontSize: 11, color: "#6b7280" }}>Loading herd…</p>
    </div>
  );
}

export default function LeaderboardPage() {
  const router = useRouter();
  const [tab, setTab] = useState("top_goats");
  const { player } = usePlayer();

  const hayQuery = useQuery({
    queryKey: ["leaderboard", "hay"],
    queryFn: () => getLeaderboard("hay"),
    staleTime: 60_000,
  });

  const weeklyQuery = useQuery({
    queryKey: ["leaderboard", "weekly_movers"],
    queryFn: getWeeklyMovers,
    staleTime: 60_000,
    enabled: tab === "weekly_movers" || tab === "my_climb",
  });

  const streakQuery = useQuery({
    queryKey: ["leaderboard", "gait"],
    queryFn: () => getLeaderboard("gait"),
    staleTime: 60_000,
    enabled: tab === "streaks" || tab === "my_climb",
  });

  const heatQuery = useQuery({
    queryKey: ["leaderboard", "heat_check"],
    queryFn: getHeatCheck,
    staleTime: 60_000,
    enabled: tab === "heat_check",
  });

  // My Climb derived values
  const myHayRank = hayQuery.data?.current_user_rank;
  const userAbove = myHayRank && myHayRank > 1
    ? hayQuery.data?.entries.find(e => e.rank === myHayRank - 1)
    : null;
  const myLifetimeHay = player?.total_hay_earned ?? 0;
  const myWeeklyHay = weeklyQuery.data?.entries.find(e => e.is_current_user)?.value ?? 0;
  const myStreak = player?.gait_streak ?? 0;
  const hayBehind = userAbove ? userAbove.value - myLifetimeHay : 0;

  // ── Tab renderers ──

  function renderTopGoats() {
    if (hayQuery.isLoading) return <LoadingState />;
    if (hayQuery.isError) return <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "24px 0" }}>Failed to load leaderboard.</p>;
    const data = hayQuery.data;
    if (!data?.entries.length) return <BoardSection label="Lifetime Hay Leaders"><p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "24px 0" }}>No Goats ranked yet. Be the first.</p></BoardSection>;
    const userInTop20 = data.entries.some(e => e.is_current_user);
    return (
      <BoardSection label="Lifetime Hay Leaders">
        {data.entries.map(entry => (
          <LeaderRow
            key={entry.user_id}
            entry={entry}
            valueDisplay={<span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>{entry.value.toLocaleString()} <span style={{ fontSize: 10, color: "#6b7280", fontWeight: 400 }}>Hay</span></span>}
          />
        ))}
        {!userInTop20 && data.current_user_rank && <UserFooter rank={data.current_user_rank} />}
      </BoardSection>
    );
  }

  function renderWeeklyMovers() {
    if (weeklyQuery.isLoading) return <LoadingState />;
    if (weeklyQuery.isError) return <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "24px 0" }}>Failed to load.</p>;
    const data = weeklyQuery.data;
    if (!data?.entries.length) return <BoardSection label="Biggest climbers in the last 7 days"><p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "24px 0" }}>No Hay earned this week yet. Get moving.</p></BoardSection>;
    const userInTop20 = data.entries.some(e => e.is_current_user);
    return (
      <BoardSection label="Biggest climbers in the last 7 days">
        {data.entries.map(entry => (
          <LeaderRow
            key={entry.user_id}
            entry={entry}
            valueDisplay={<span style={{ fontSize: 13, color: "#53c660", fontWeight: 600 }}>+{entry.value.toLocaleString()} <span style={{ fontSize: 10, color: "#6b7280", fontWeight: 400 }}>Hay this week</span></span>}
          />
        ))}
        {!userInTop20 && data.current_user_rank && <UserFooter rank={data.current_user_rank} />}
      </BoardSection>
    );
  }

  function renderStreaks() {
    if (streakQuery.isLoading) return <LoadingState />;
    if (streakQuery.isError) return <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "24px 0" }}>Failed to load.</p>;
    const data = streakQuery.data;
    if (!data?.entries.length) return <BoardSection label="GAIT Streak Leaderboard"><p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "24px 0" }}>No active streaks. Start one today.</p></BoardSection>;
    const userInTop20 = data.entries.some(e => e.is_current_user);
    return (
      <BoardSection label="GAIT Streak Leaderboard">
        {data.entries.map(entry => {
          const tier = streakTierLabel(entry.value);
          return (
            <LeaderRow
              key={entry.user_id}
              entry={entry}
              valueDisplay={<span style={{ fontSize: 13, color: "#f97316", fontWeight: 600 }}>{flameCount(entry.value)} {entry.value}d</span>}
              valueSub={tier ? <span style={{ fontSize: 10, color: "#9ca3af" }}>{tier}</span> : undefined}
            />
          );
        })}
        {!userInTop20 && data.current_user_rank && <UserFooter rank={data.current_user_rank} />}
      </BoardSection>
    );
  }

  function renderHeatCheck() {
    if (heatQuery.isLoading) return <LoadingState />;
    if (heatQuery.isError) return <p style={{ fontSize: 12, color: "#ef4444", textAlign: "center", padding: "24px 0" }}>Failed to load.</p>;
    const data = heatQuery.data;
    return (
      <BoardSection label="Today&apos;s Haymakers">
        {!data?.entries.length ? (
          <p style={{ fontSize: 12, color: "#4b5563", textAlign: "center", padding: "24px 0" }}>
            The pasture is quiet today. Be the first to move.
          </p>
        ) : (
          <>
            {data.entries.map(entry => (
              <LeaderRow
                key={entry.user_id}
                entry={entry}
                valueDisplay={<span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>+{entry.value.toLocaleString()} <span style={{ fontSize: 10, color: "#6b7280", fontWeight: 400 }}>Hay today</span></span>}
              />
            ))}
            {!data.entries.some(e => e.is_current_user) && data.current_user_rank && <UserFooter rank={data.current_user_rank} />}
          </>
        )}
      </BoardSection>
    );
  }

  function renderMyClimb() {
    if (hayQuery.isLoading || weeklyQuery.isLoading) return <LoadingState />;
    return (
      <div className="flex flex-col gap-4">
        {/* Head to Head */}
        <div className="rounded-xl border border-goat-border p-4" style={{ background: "rgba(13,13,26,0.7)" }}>
          <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>▸ Head to Head</p>
          {myHayRank === 1 ? (
            <p style={{ fontSize: 14, color: "#53c660", fontWeight: 700, textAlign: "center", padding: "12px 0" }}>
              You are the Top Goat. Defend your pasture. 🐐
            </p>
          ) : (
            <>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "10px 14px", borderRadius: 8, marginBottom: 8,
                background: "rgba(97,0,255,0.08)", borderLeft: "3px solid #7c3aed",
              }}>
                <span style={{ fontSize: 13, color: "#a78bfa", fontWeight: 700 }}>
                  You {myHayRank ? `(#${myHayRank})` : ""}
                </span>
                <span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>
                  {myLifetimeHay.toLocaleString()} Hay
                </span>
              </div>

              {userAbove ? (
                <>
                  <div style={{ textAlign: "center", marginBottom: 8 }}>
                    <p style={{ fontSize: 11, color: "#f59e0b" }}>
                      ↑ You are <strong>{hayBehind.toLocaleString()}</strong> Hay behind <strong>{userAbove.display_name}</strong>
                    </p>
                  </div>
                  <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "10px 14px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)", borderLeft: "3px solid transparent",
                  }}>
                    <span style={{ fontSize: 13, color: "#F5F5F5" }}>
                      {userAbove.display_name} <span style={{ color: "#6b7280", fontSize: 11 }}>(#{userAbove.rank})</span>
                    </span>
                    <span style={{ fontSize: 13, color: "#f59e0b", fontWeight: 600 }}>
                      {userAbove.value.toLocaleString()} Hay
                    </span>
                  </div>
                </>
              ) : myHayRank && myHayRank > 1 ? (
                <p style={{ fontSize: 11, color: "#6b7280", textAlign: "center", padding: "8px 0" }}>
                  The goat ahead of you is outside the top 20.
                </p>
              ) : null}
            </>
          )}
        </div>

        {/* Personal stats */}
        <div className="rounded-xl border border-goat-border p-4" style={{ background: "rgba(13,13,26,0.7)" }}>
          <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 12 }}>▸ Your Climb</p>
          <div className="grid grid-cols-2 gap-3">
            <StatTile label="Lifetime Hay" value={myLifetimeHay.toLocaleString()} color="#f59e0b" />
            <StatTile label="Hay This Week" value={`+${myWeeklyHay.toLocaleString()}`} color="#53c660" />
            <StatTile label="GAIT Streak" value={`${myStreak}d`} color="#8B5CF6" />
            <StatTile label="Lifetime Rank" value={myHayRank ? `#${myHayRank}` : "—"} color="#a78bfa" />
          </div>
        </div>
      </div>
    );
  }

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

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              fontSize: 11, padding: "5px 14px", borderRadius: 99, fontWeight: 600, cursor: "pointer",
              background: tab === t.key ? "rgba(97,0,255,0.35)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${tab === t.key ? "rgba(97,0,255,0.55)" : "rgba(255,255,255,0.1)"}`,
              color: tab === t.key ? "#a78bfa" : "#6b7280",
              transition: "all 0.15s",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "top_goats"     && renderTopGoats()}
      {tab === "weekly_movers" && renderWeeklyMovers()}
      {tab === "streaks"       && renderStreaks()}
      {tab === "heat_check"    && renderHeatCheck()}
      {tab === "my_climb"      && renderMyClimb()}
    </div>
  );
}
