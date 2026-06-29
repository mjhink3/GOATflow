"use client";

import { useState, useEffect, type CSSProperties } from "react";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { usePlayer } from "@/lib/hooks/usePlayer";
import { useHorns } from "@/lib/hooks/useHorns";
import { pasture_name, ascension_rank } from "@/lib/gamification";

const LEVEL_IMAGES: Record<number, string> = {
  1: "/assets/GOATflow_The_Kid_level_1_1773616494954.webp",
  2: "/assets/GOATflow_The_Starter_level_2_1773616494956.webp",
  3: "/assets/GOATflow_The_Builder_level_3_1773616494949.webp",
  4: "/assets/WorkGOAT_The_Climber_level_4_1773616494957.webp",
  5: "/assets/GOATflow_The_Leader_level_5_1773616494955.webp",
  6: "/assets/GOATflow_The_Visionary_level_6_1773616494957.webp",
  7: "/assets/GOATflow_The_G.O.A.T._level_7_1773616494953.webp",
};

const LEVEL_BITE_PX: Record<number, number> = {
  1: 0, 2: 12, 3: 17, 4: 22, 5: 28, 6: 36, 7: 46,
};

function getLevelBiteStyle(level: number): CSSProperties {
  const r = LEVEL_BITE_PX[Math.min(level, 7)] ?? 0;
  if (r === 0) return {};
  const pct = Math.round((r / 80) * 100);
  return {
    clipPath: `polygon(0% 0%, ${100 - pct}% 0%, 100% ${pct}%, 100% 100%, 0% 100%)`,
  };
}

const QUICK_SCRIPTS = [
  { label: "Staffing Crunch",  text: "IF staffing < 85% THEN set all Logistics tasks to Priority 1." },
  { label: "Legal First",       text: "ALWAYS prioritize tasks with legal deadlines over general admin." },
  { label: "Family Saturdays",  text: "Saturdays are for family—move all work tasks to Medium Priority unless labeled EMERGENCY." },
  { label: "Family Events",     text: "Family events are always Priority 1." },
  { label: "Tuesday Focus",     text: "Focus on Labor Relations on Tuesdays." },
];

const WEEK_LABELS = ["Wk -3", "Wk -2", "Wk -1", "This Wk"];

function ClipBar({ pct }: { pct: number | null }) {
  if (pct === null || pct === 0) {
    const color = "#4b5563";
    return (
      <span style={{ fontFamily: "monospace", color, letterSpacing: "0.05em" }}>
        {"░".repeat(10)}
        <span style={{ color: "#6b7280", marginLeft: 6 }}>0%</span>
      </span>
    );
  }
  const filled = Math.min(10, Math.max(0, Math.round(pct / 10)));
  const color = pct >= 75 ? "#53c660" : pct >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <span style={{ fontFamily: "monospace", color, letterSpacing: "0.05em" }}>
      {"█".repeat(filled)}{"░".repeat(10 - filled)}
      <span style={{ color: "#9ca3af", marginLeft: 6 }}>{pct}%</span>
    </span>
  );
}

interface SidebarProps {
  isMobileOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isMobileOpen = false, onClose }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const onTrail = pathname === "/trail";
  const { user, logout } = useAuth();
  const { player } = usePlayer();
  const { horns, save, isSaving } = useHorns();

  const [localHorns, setLocalHorns] = useState<string[] | null>(null);
  const [newHorn, setNewHorn]         = useState("");
  const [copied, setCopied]           = useState<number | null>(null);
  const [goatifOn, setGoatifOn]       = useState(false);

  useEffect(() => {
    setGoatifOn(localStorage.getItem("goatflow_notif_master") === "true");
  }, []);

  const activeHorns = localHorns ?? horns;
  const level    = player?.level ?? 1;
  const levelImg = LEVEL_IMAGES[Math.min(level, 7)] ?? LEVEL_IMAGES[7];
  const rank     = ascension_rank(level);
  const pasture  = pasture_name(level);
  const clipPct     = player?.weekly_clip_rate != null ? Math.round(player.weekly_clip_rate * 100) : null;
  const clipColor   = clipPct == null ? "#6b7280" : clipPct >= 75 ? "#53c660" : clipPct >= 50 ? "#f59e0b" : "#ef4444";
  const clipDisplay = clipPct != null ? `${clipPct}%` : "—";

  const weeklyRates: (number | null)[] = player?.weekly_clip_rates ?? [null, null, null, null];

  const linkedInText = encodeURIComponent(
    `I'm Level ${level} on GOATflow — ${rank} in the ${pasture}. Building my GOAT legacy one track at a time. 🐐 #GOATflow #Productivity`
  );
  const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent("https://goatflow.app")}&summary=${linkedInText}`;

  function addHorn() {
    const trimmed = newHorn.trim();
    if (!trimmed || activeHorns.length >= 10) return;
    setLocalHorns([...activeHorns, trimmed]);
    setNewHorn("");
  }

  function removeHorn(i: number) {
    setLocalHorns(activeHorns.filter((_, idx) => idx !== i));
  }

  async function lockInHorns() {
    await save(activeHorns);
    setLocalHorns(null);
  }

  function copyScript(text: string, idx: number) {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 1500);
  }

  function toggleGoatif() {
    const next = !goatifOn;
    setGoatifOn(next);
    localStorage.setItem("goatflow_notif_master", String(next));
  }

  return (
    <>
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 md:hidden" onClick={onClose} />
      )}
    <aside
      className={`relative flex flex-col w-64 bg-goat-surface border-r border-goat-border overflow-y-auto shrink-0 min-h-screen ${isMobileOpen ? "fixed inset-y-0 left-0 z-50" : "hidden md:flex"}`}
      style={{ scrollbarWidth: "none", msOverflowStyle: "none" } as CSSProperties}
    >

      {/* ── Mobile close button ── */}
      {isMobileOpen && (
        <button
          className="md:hidden absolute top-3 right-3 z-10 flex items-center justify-center w-8 h-8 rounded-lg"
          style={{ background: "rgba(255,255,255,0.06)", border: "1px solid #2A2A4A", color: "#9ca3af", fontSize: 16 }}
          onClick={onClose}
          aria-label="Close menu"
        >
          ✕
        </button>
      )}

      {/* ── Branding header ── */}
      <div className="border-b border-goat-border">
        <Image
          src="/icons/goatflow_logo_nobg.webp"
          alt="GOATflow"
          width={256}
          height={120}
          loading="eager"
          style={{ width: "100%", height: "auto", display: "block" }}
        />
      </div>

      {/* ── User avatar + rank ── */}
      <div className="flex flex-col items-center px-4 py-4 border-b border-goat-border gap-2">
        <div style={{ position: "relative", width: 84, height: 84, flexShrink: 0 }}>
          <div style={{
            width: 80,
            height: 80,
            margin: 2,
            borderRadius: 12,
            backgroundImage: `url(${levelImg})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            border: "2px solid #7c3aed",
          }} />
          {level >= 2 && (
            <div style={{
              position: "absolute",
              top: -2,
              right: -2,
              width: Math.max(LEVEL_BITE_PX[Math.min(level, 7)] * 2, 20),
              height: Math.max(LEVEL_BITE_PX[Math.min(level, 7)] * 2, 20),
              borderRadius: "50%",
              background: "#0D0D1A",
              zIndex: 10,
            }} />
          )}
        </div>
        <p className="font-syne text-goat-white font-bold text-sm text-center leading-tight">
          {user?.display_name ?? "—"}
        </p>
        <span style={{
          fontSize: 9, padding: "2px 8px", borderRadius: 99,
          background: "rgba(124,58,237,0.25)", color: "#a78bfa",
          border: "1px solid rgba(124,58,237,0.4)", textTransform: "uppercase", letterSpacing: "0.1em"
        }}>
          Lv {level} · {pasture}
        </span>
      </div>

      {/* ── Stats ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <div style={{
          background: "rgba(13,13,26,0.8)",
          border: "1px solid #2A2A4A",
          borderRadius: 12,
          padding: "12px 14px",
        }}>
          <p style={{ fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: 13, color: "#F5F5F5", marginBottom: 10 }}>
            🚀 My Stats
          </p>

          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_hay_stack.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> Lifetime Hay</span>
            <span style={{ fontSize: 11, color: "#53c660", fontWeight: 600 }}>{player?.total_hay_earned ?? 0}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_level.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> Ascension Rank</span>
            <span style={{ fontSize: 11, color: "#F5F5F5", fontWeight: 600 }}>{rank}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 11, color: "#9ca3af" }}>Next Fence</span>
            <span style={{ fontSize: 11, color: "#F5F5F5", fontWeight: 600 }}>{player?.hay_this_level ?? 0}/{player?.hay_to_next_level ?? 500} Hay</span>
          </div>

          <div style={{ borderTop: "1px solid #2A2A4A", marginBottom: 10 }} />

          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_hay.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> Hay Balance</span>
            <span style={{ fontSize: 11, color: "#f59e0b", fontWeight: 600 }}>{player?.hay ?? 0}/500</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}>Fresh Cheese Banked</span>
            <span style={{ fontSize: 11, color: "#F5F5F5", fontWeight: 600, display: "flex", alignItems: "center" }}><Image src="/icons/icon_fresh_cheese.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> {player?.fresh_cheese ?? 0}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_clip_rate.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> Clip Rate (7d)</span>
            <span style={{ fontSize: 11, color: clipPct === null ? "#6b7280" : clipColor, fontWeight: 600 }}>{clipDisplay}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_gait.webp" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> GAIT Streak 🔥</span>
            <span style={{ fontSize: 11, color: "#8B5CF6", fontWeight: 600 }}>
              {player?.gait_streak ?? 0}d{(player?.streak_shields ?? 0) > 0 ? ` 🛡️ ${player?.streak_shields}` : ""}
            </span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: "#9ca3af", display: "flex", alignItems: "center" }}><Image src="/icons/icon_stakes.png" width={20} height={20} alt="" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} /> Stake Streak</span>
            <span style={{ fontSize: 11, color: (player?.stake_streak ?? 0) > 0 ? "#f59e0b" : "#6b7280", fontWeight: 600 }}>
              {(player?.stake_streak ?? 0) > 0 ? `${player?.stake_streak}d` : "—"}
            </span>
          </div>

        </div>
      </div>

      {/* ── Weekly Clip Rate bars ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 8 }}>
          ▸ Clip Rate — Last 4 Weeks
        </p>
        {WEEK_LABELS.map((label, i) => {
          const rate = weeklyRates[i];
          const pct  = (rate != null && rate > 0) ? Math.round(rate * 100) : (rate === 0 ? 0 : null);
          return (
            <div key={i} className="flex items-center gap-2 py-0.5">
              <span style={{ fontSize: 9, color: "#6b7280", width: 44, flexShrink: 0 }}>{label}</span>
              <ClipBar pct={pct} />
            </div>
          );
        })}
      </div>

      {/* ── LinkedIn Share ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <a
          href={linkedInUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border text-xs font-semibold uppercase tracking-widest transition-colors"
          style={{
            borderColor: "rgba(0,119,181,0.4)", color: "#0ea5e9",
            background: "rgba(0,119,181,0.08)", display: "flex",
          }}
        >
          🔗 Share on LinkedIn
        </a>
      </div>

      {/* ── GOAT Horns ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 8 }}>
          ▸ GOAT Horns ({activeHorns.length}/10) — influenced {player?.horn_influence_count ?? 0} tracks
        </p>
        <div className="flex flex-col gap-1 mb-2">
          {activeHorns.length === 0 && (
            <p style={{ fontSize: 10, color: "#6b7280", fontStyle: "italic" }}>No horns set. Add one below.</p>
          )}
          {activeHorns.map((h, i) => (
            <div key={i} className="flex items-start gap-1 group">
              <p style={{ fontSize: 10, color: "#c4b5fd", flex: 1, lineHeight: 1.4 }}>
                <span style={{ color: "#6100ff", marginRight: 4 }}>◆</span>{h}
              </p>
              <button
                onClick={() => removeHorn(i)}
                className="text-goat-red opacity-0 group-hover:opacity-70 transition-opacity shrink-0 mt-0.5"
                style={{ fontSize: 10 }}
                title="Remove horn"
              >✕</button>
            </div>
          ))}
        </div>
        {activeHorns.length < 10 && (
          <div className="flex gap-1 mb-2">
            <input
              value={newHorn}
              onChange={e => setNewHorn(e.target.value)}
              onKeyDown={e => e.key === "Enter" && addHorn()}
              placeholder="Add a horn directive…"
              style={{
                flex: 1, background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.25)",
                borderRadius: 6, padding: "4px 8px", fontSize: 10, color: "#F5F5F5", outline: "none"
              }}
            />
            <button
              onClick={addHorn}
              style={{
                background: "rgba(97,0,255,0.3)", border: "1px solid rgba(97,0,255,0.5)",
                borderRadius: 6, padding: "4px 8px", fontSize: 10, color: "#a78bfa", cursor: "pointer"
              }}
            >+</button>
          </div>
        )}
        <button
          onClick={lockInHorns}
          disabled={isSaving}
          className="w-full py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest transition-colors"
          style={{
            background: isSaving ? "rgba(97,0,255,0.15)" : "rgba(97,0,255,0.25)",
            border: "1px solid rgba(97,0,255,0.5)",
            color: "#a78bfa", cursor: isSaving ? "not-allowed" : "pointer"
          }}
        >
          {isSaving ? "Saving…" : "🔒 Lock In My Horns"}
        </button>
      </div>

      {/* ── Quick Scripts ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em", marginBottom: 8 }}>
          ▸ QUICK SCRIPTS
        </p>
        <div className="flex flex-col gap-1.5">
          {QUICK_SCRIPTS.map((qs, i) => (
            <div key={i} className="flex items-center justify-between gap-1">
              <span style={{ fontSize: 10, color: "#9ca3af" }}>{qs.label}</span>
              <button
                onClick={() => copyScript(qs.text, i)}
                style={{
                  fontSize: 9, padding: "2px 6px", borderRadius: 4,
                  background: copied === i ? "rgba(83,198,96,0.2)" : "rgba(97,0,255,0.15)",
                  border: `1px solid ${copied === i ? "rgba(83,198,96,0.4)" : "rgba(97,0,255,0.3)"}`,
                  color: copied === i ? "#53c660" : "#a78bfa", cursor: "pointer", whiteSpace: "nowrap"
                }}
              >
                {copied === i ? "Copied!" : "Copy"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Leaderboard ── */}
      <div className="px-4 py-2 border-b border-goat-border">
        <button
          className="w-full flex items-center gap-2 py-2 px-3 rounded-lg border border-goat-border text-xs text-goat-silver hover:border-goat-violet hover:text-goat-violet transition-colors"
          onClick={() => { router.push("/leaderboard"); onClose?.(); }}
        >
          <Image src="/icons/icon_completed.webp" alt="" width={14} height={14} />
          🏆 Leaderboard
        </button>
      </div>

      {/* ── Trail Notes ── */}
      <div className="px-4 py-3 border-b border-goat-border">
        <button
          className="w-full flex items-center gap-2 py-2 px-3 rounded-lg border border-goat-border text-xs text-goat-silver hover:border-goat-violet hover:text-goat-violet transition-colors"
          onClick={() => router.push(onTrail ? "/dashboard" : "/trail")}
        >
          <Image src="/icons/icon_trail_notes.webp" alt="" width={14} height={14} />
          {onTrail ? "← Dashboard" : "Trail Notes"}
        </button>
      </div>

      {/* ── Spacer ── */}
      <div className="flex-1" />

      {/* ── Goatifications toggle ── */}
      <div className="px-4 py-3 border-t border-goat-border">
        <div className="flex items-center justify-between mb-1">
          <p style={{ fontSize: 9, color: "#6100ff", textTransform: "uppercase", letterSpacing: "0.15em" }}>
            ▸ Goatifications
          </p>
          <button
            onClick={toggleGoatif}
            aria-label="Toggle goatifications"
            style={{
              width: 34, height: 19, borderRadius: 99, cursor: "pointer",
              position: "relative", flexShrink: 0,
              background: goatifOn ? "rgba(97,0,255,0.55)" : "rgba(255,255,255,0.1)",
              border: `1px solid ${goatifOn ? "rgba(97,0,255,0.7)" : "rgba(255,255,255,0.2)"}`,
              transition: "background 0.2s, border-color 0.2s",
            }}
          >
            <span style={{
              position: "absolute", top: 3, left: goatifOn ? 16 : 3,
              width: 11, height: 11, borderRadius: "50%",
              background: goatifOn ? "#a78bfa" : "#6b7280",
              transition: "left 0.2s",
            }} />
          </button>
        </div>
        <p style={{ fontSize: 9, color: "#4b5563" }}>
          {goatifOn ? "Notifications ON" : "Notifications OFF"}
        </p>
      </div>

      {/* ── Logout ── */}
      <div className="px-4 pb-4 border-t border-goat-border pt-3">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 py-2 px-3 rounded-lg border border-goat-border text-xs text-goat-red hover:bg-goat-red/10 hover:border-goat-red transition-colors"
        >
          <Image src="/icons/icon_logout.png" alt="" width={14} height={14} />
          Logout
        </button>
      </div>
    </aside>
    </>
  );
}
