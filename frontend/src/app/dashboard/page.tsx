"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { useSignals } from "@/lib/hooks/useSignals";
import { useStakes } from "@/lib/hooks/useStakes";
import { runChurn } from "@/lib/api/churn";
import { useQueryClient } from "@tanstack/react-query";
import { StatsRow } from "@/components/dashboard/StatsRow";
import { TrackCard } from "@/components/dashboard/TrackCard";
import { HayPopup } from "@/components/dashboard/HayPopup";
import { FreshCheesePopup } from "@/components/dashboard/FreshCheesePopup";
import { TrailNotePrompt } from "@/components/dashboard/TrailNotePrompt";
import { TrackRatingPrompt } from "@/components/dashboard/TrackRatingPrompt";
import { CancelReasonPrompt } from "@/components/dashboard/CancelReasonPrompt";
import type { CompletionResult } from "@/lib/types";

const CHURN_DAILY_LIMIT = 15;

export default function DashboardPage() {
  const qc = useQueryClient();
  const { signals, complete, cancel, isLoading: signalsLoading } = useSignals();
  const { todayStake, yesterdayStake, isLoadingToday, create: createStake, claim: claimStake } = useStakes();

  // ── Morning Stake gate ──
  const [stakeText, setStakeText]       = useState("");
  const [stakePending, setStakePending] = useState(false);
  const [gateSkipped, setGateSkipped]   = useState(false);
  const [claimPending, setClaimPending] = useState(false);
  const [claimDone, setClaimDone]       = useState(false);

  // ── Track Sieve ──
  const [sieverText, setSieverText]         = useState("");
  const [sieverFiles, setSieverFiles]       = useState<File[]>([]);
  const [isDragging, setIsDragging]         = useState(false);
  const [isChurning, setIsChurning]         = useState(false);
  const [churnCount, setChurnCount]         = useState(0);
  const [churnError, setChurnError]         = useState("");
  const [rejectedInputs, setRejectedInputs] = useState<string[]>([]);
  const [signalWarning, setSignalWarning]   = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Completion popups ──
  const [completionResult, setCompletionResult]     = useState<CompletionResult | null>(null);
  const [completionCreatedAt, setCompletionCreatedAt] = useState<string | null>(null);
  const [trailNoteData, setTrailNoteData]           = useState<{ logId: number; taskName: string; daysElapsed: number; tier: string } | null>(null);
  const [ratingData, setRatingData]                 = useState<{ logId: number; taskName: string; tier: string } | null>(null);
  const [pendingCheese, setPendingCheese]           = useState<{ count: number; total: number } | null>(null);
  const [showCheese, setShowCheese]                 = useState(false);
  const [cancelResult, setCancelResult]             = useState<{ taskName: string; logId: number | null } | null>(null);

  // ─────────────────────────────────────────────────────────────────────────
  // Morning Stake Gate
  // ─────────────────────────────────────────────────────────────────────────
  const needsGate = !isLoadingToday && !todayStake && !gateSkipped;

  // When stake is already done on mount, signal tour to start
  useEffect(() => {
    if (!isLoadingToday && !needsGate) {
      const t = setTimeout(() => window.dispatchEvent(new CustomEvent("goatflow:stake-done")), 100);
      return () => clearTimeout(t);
    }
  }, [isLoadingToday, needsGate]);

  async function handleStake() {
    const text = stakeText.trim() || "—";
    setStakePending(true);
    try {
      await createStake(text);
      window.dispatchEvent(new CustomEvent("goatflow:stake-done"));
    } catch (err) {
      console.error("[stake] failed:", err);
    } finally {
      setStakePending(false);
    }
  }

  async function handleClaim() {
    setClaimPending(true);
    try {
      const res = await claimStake();
      setClaimDone(true);
      window.alert(`🏆 Yesterday's stake claimed!\n+${res.hay_earned} Hay earned.`);
    } catch (err) {
      console.error("[claim] failed:", err);
    } finally {
      setClaimPending(false);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Churn Engine
  // ─────────────────────────────────────────────────────────────────────────
  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = Array.from(e.dataTransfer.files);
    if (dropped.length) setSieverFiles(prev => [...prev, ...dropped]);
  }

  async function handleChurn() {
    if (churnCount >= CHURN_DAILY_LIMIT) {
      setChurnError(`Daily limit reached (${CHURN_DAILY_LIMIT} churns/day). Come back tomorrow.`);
      return;
    }
    if (!sieverText.trim() && sieverFiles.length === 0) {
      setChurnError("Paste some text or attach a file before churning.");
      return;
    }
    setChurnError("");
    setRejectedInputs([]);
    setSignalWarning("");
    setIsChurning(true);
    try {
      const result = await runChurn(sieverFiles, sieverText);
      setChurnCount(c => c + 1);
      setSieverText("");
      setSieverFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (result.rejected_inputs?.length > 0) setRejectedInputs(result.rejected_inputs);
      if (result.signal_warning) setSignalWarning(result.signal_warning);
      qc.invalidateQueries({ queryKey: ["signals"] });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setChurnError(typeof detail === "string" ? detail : "Churn failed. Check the console.");
      console.error("[churn] failed:", err);
    } finally {
      setIsChurning(false);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Completion popup flow
  // ─────────────────────────────────────────────────────────────────────────
  function handleTrackCompleted(result: CompletionResult, createdAt: string) {
    setCompletionResult(result);
    setCompletionCreatedAt(createdAt);
  }

  function handleHayConfirm() {
    const cheese = completionResult?.cheese_gained ?? 0;
    const cheeseTotal = completionResult?.cheese_total ?? 0;
    const logId = completionResult?.log_id ?? 0;
    const taskName = completionResult?.task_name ?? "";
    const tier = completionResult?.xp_tier ?? "Standard";
    const elapsed = completionCreatedAt
      ? Math.max(0, Math.floor((Date.now() - new Date(completionCreatedAt).getTime()) / (1000 * 60 * 60 * 24)))
      : 0;
    setCompletionResult(null);
    setCompletionCreatedAt(null);
    if (cheese > 0) setPendingCheese({ count: cheese, total: cheeseTotal });
    setTrailNoteData({ logId, taskName, daysElapsed: elapsed, tier });
  }

  function handleTrailNoteClose() {
    const data = trailNoteData;
    setTrailNoteData(null);
    const count = (parseInt(localStorage.getItem("goatflow_completion_count") || "0", 10) || 0) + 1;
    localStorage.setItem("goatflow_completion_count", String(count));
    if (count % 3 === 0 && data) {
      setRatingData({ logId: data.logId, taskName: data.taskName, tier: data.tier });
    } else {
      if (pendingCheese) setShowCheese(true);
    }
  }

  function handleRatingClose() {
    setRatingData(null);
    if (pendingCheese) setShowCheese(true);
  }

  function handleTrackCancelled(taskName: string, logId: number | null) {
    setCancelResult({ taskName, logId });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="relative flex-1 flex flex-col" style={{ minHeight: "100vh" }}>

      {/* ── Completion popups ── */}
      {completionResult && (
        <HayPopup result={completionResult} onConfirm={handleHayConfirm} />
      )}
      {trailNoteData && !completionResult && (
        <TrailNotePrompt
          taskName={trailNoteData.taskName}
          logId={trailNoteData.logId}
          daysElapsed={trailNoteData.daysElapsed}
          onDismiss={handleTrailNoteClose}
        />
      )}
      {cancelResult && (
        <CancelReasonPrompt
          taskName={cancelResult.taskName}
          logId={cancelResult.logId}
          onDone={() => setCancelResult(null)}
        />
      )}
      {ratingData && !completionResult && !trailNoteData && (
        <TrackRatingPrompt
          taskName={ratingData.taskName}
          tier={ratingData.tier}
          logId={ratingData.logId}
          onDismiss={handleRatingClose}
        />
      )}
      {showCheese && !completionResult && !trailNoteData && !ratingData && (
        <FreshCheesePopup
          count={pendingCheese?.count ?? 1}
          total={pendingCheese?.total ?? 1}
          onConfirm={() => {
            setShowCheese(false);
            setPendingCheese(null);
          }}
        />
      )}

      {/* ── Morning Stake Gate ── */}
      {needsGate && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: "rgba(8,8,15,0.96)", backdropFilter: "blur(4px)" }}
        >
          <div
            className="w-full max-w-md mx-4 rounded-2xl border border-goat-border p-8 animate-gf-pop-in"
            style={{ background: "rgba(13,13,26,0.97)" }}
          >
            {yesterdayStake?.status === "active" && !claimDone && (
              <div className="mb-6 px-4 py-3 rounded-xl border" style={{ background: "rgba(83,198,96,0.1)", borderColor: "rgba(83,198,96,0.35)" }}>
                <p style={{ fontSize: 12, color: "#53c660", marginBottom: 6 }}>
                  🏆 Yesterday&apos;s stake is waiting to be claimed!
                </p>
                <p style={{ fontSize: 10, color: "#9ca3af", marginBottom: 8, fontStyle: "italic" }}>
                  &ldquo;{yesterdayStake.stake_text}&rdquo;
                </p>
                <button
                  onClick={handleClaim}
                  disabled={claimPending}
                  style={{
                    fontSize: 11, padding: "6px 16px", borderRadius: 8, fontWeight: 700,
                    background: "rgba(83,198,96,0.25)", border: "1px solid rgba(83,198,96,0.5)",
                    color: "#53c660", cursor: claimPending ? "not-allowed" : "pointer",
                  }}
                >
                  {claimPending ? "Claiming…" : "Claim Hay →"}
                </button>
              </div>
            )}

            <div className="flex items-center gap-3 mb-2">
              <Image src="/icons/icon_stakes.png" alt="" width={28} height={28} />
              <h2 className="font-syne text-goat-white font-bold" style={{ fontSize: 18 }}>Morning Stake</h2>
            </div>
            <p style={{ fontSize: 11, color: "#9ca3af", marginBottom: 20, lineHeight: 1.6 }}>
              What&apos;s the one thing you&apos;re staking your day on? Setting a stake keeps you accountable and earns Hay at day&apos;s end.
            </p>

            <textarea
              value={stakeText}
              onChange={e => setStakeText(e.target.value)}
              placeholder="e.g. I will close the partnership deal with Apex by 5pm."
              rows={3}
              style={{
                width: "100%", background: "rgba(97,0,255,0.08)", border: "1px solid rgba(97,0,255,0.3)",
                borderRadius: 10, padding: "10px 12px", fontSize: 12, color: "#F5F5F5",
                outline: "none", resize: "vertical", marginBottom: 14, fontFamily: "inherit",
              }}
            />

            <div className="flex gap-3">
              <button
                onClick={handleStake}
                disabled={stakePending}
                className="flex-1 py-3 rounded-xl font-bold text-sm uppercase tracking-widest"
                style={{
                  background: stakePending ? "rgba(97,0,255,0.25)" : "rgba(97,0,255,0.45)",
                  border: "1px solid rgba(97,0,255,0.6)",
                  color: "#a78bfa", cursor: stakePending ? "not-allowed" : "pointer",
                }}
              >
                {stakePending ? "Staking…" : "🔒 Stake It"}
              </button>
              <button
                onClick={() => { setGateSkipped(true); window.dispatchEvent(new CustomEvent("goatflow:stake-done")); }}
                style={{
                  padding: "12px 20px", borderRadius: 10, fontSize: 11, color: "#6b7280",
                  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                  cursor: "pointer",
                }}
              >
                Skip today
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Main dashboard content ── */}
      <div className="flex flex-col gap-5 p-5 pb-16 pt-14 md:pt-5">

          {/* ── Stats Row ── */}
          <StatsRow />

          {/* ── Track Sieve ── */}
          <section
            className="rounded-2xl border border-goat-border p-4 track-sieve-section"
            style={{ background: "rgba(13,13,26,0.6)" }}
          >
            <div className="flex items-center gap-2 mb-4">
              <Image src="/icons/icon_track_sieve.png" alt="" width={44} height={44} />
              <h2 className="font-syne text-goat-white font-bold" style={{ fontSize: 18 }}>Track Sieve</h2>
              <span style={{
                marginLeft: "auto", fontSize: 11, color: "#6b7280",
                background: "rgba(97,0,255,0.1)", border: "1px solid rgba(97,0,255,0.2)",
                borderRadius: 99, padding: "2px 8px",
              }}>
                {churnCount}/{CHURN_DAILY_LIMIT} used today
              </span>
            </div>

            {/* Two-column input layout */}
            <div className="grid grid-cols-2 gap-3 mb-4">

              {/* Left: drag-and-drop file zone */}
              <div
                onDrop={handleDrop}
                onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center justify-center gap-2 rounded-xl cursor-pointer transition-colors"
                style={{
                  border: `2px dashed ${isDragging ? "rgba(97,0,255,0.7)" : "rgba(97,0,255,0.3)"}`,
                  background: isDragging ? "rgba(97,0,255,0.1)" : "rgba(97,0,255,0.03)",
                  minHeight: 140, padding: "16px 12px",
                  transition: "border-color 0.15s, background 0.15s",
                }}
              >
                <span style={{ fontSize: 22 }}>📂</span>
                <p style={{ fontSize: 14, color: "#a78bfa", textAlign: "center", fontWeight: 600 }}>
                  Drag and drop files here
                </p>
                <p style={{ fontSize: 11, color: "#6b7280", textAlign: "center", lineHeight: 1.5 }}>
                  Limit 200MB per file<br />PDF, PNG, JPG, WEBP, DOCX, TXT
                </p>
                {sieverFiles.length > 0 && (
                  <p style={{ fontSize: 10, color: "#53c660", textAlign: "center" }}>
                    {sieverFiles.length} file{sieverFiles.length > 1 ? "s" : ""} selected
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        setSieverFiles([]);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      style={{ marginLeft: 6, color: "#ef4444", background: "none", border: "none", cursor: "pointer", fontSize: 10 }}
                    >
                      ✕
                    </button>
                  </p>
                )}
                <button
                  onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
                  style={{
                    marginTop: 4, padding: "5px 14px", borderRadius: 8, fontSize: 12,
                    background: "rgba(97,0,255,0.2)", border: "1px solid rgba(97,0,255,0.4)",
                    color: "#a78bfa", cursor: "pointer",
                  }}
                >
                  Browse files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.txt"
                  onChange={e => setSieverFiles(Array.from(e.target.files ?? []))}
                  style={{ display: "none" }}
                />
              </div>

              {/* Right: text input */}
              <textarea
                value={sieverText}
                onChange={e => setSieverText(e.target.value)}
                placeholder="Paste emails, notes, chat logs, or just type what's on your mind…"
                style={{
                  width: "100%", height: "100%", minHeight: 140,
                  background: "rgba(97,0,255,0.05)", border: "1px solid rgba(97,0,255,0.2)",
                  borderRadius: 10, padding: "10px 12px", fontSize: 14, color: "#F5F5F5",
                  outline: "none", resize: "none", fontFamily: "inherit",
                }}
              />
            </div>

            {churnError && (
              <p style={{ fontSize: 11, color: "#ef4444", marginBottom: 8 }}>{churnError}</p>
            )}

            <button
              onClick={handleChurn}
              disabled={isChurning || churnCount >= CHURN_DAILY_LIMIT}
              className="flex items-center justify-center gap-2 w-full py-4 rounded-xl font-bold uppercase tracking-widest transition-colors disabled:opacity-40"
              style={{
                fontSize: 16,
                background: isChurning ? "rgba(97,0,255,0.2)" : "rgba(97,0,255,0.35)",
                border: "1px solid rgba(97,0,255,0.55)",
                color: "#a78bfa", cursor: isChurning ? "not-allowed" : "pointer",
              }}
            >
              <Image src="/icons/icon_churn_engine.png" alt="" width={40} height={40} />
              {isChurning ? "Churning…" : "Drop Into Churn Engine"}
            </button>

            {rejectedInputs.length > 0 && (
              <div style={{ marginTop: 12, padding: "10px 14px", borderRadius: 8, background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)" }}>
                <p style={{ fontSize: 12, color: "#f59e0b", marginBottom: 6, fontWeight: 600 }}>🐐 Some inputs needed more signal:</p>
                <ul style={{ paddingLeft: 16, margin: 0 }}>
                  {rejectedInputs.map((input, i) => (
                    <li key={i} style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>{input}</li>
                  ))}
                </ul>
                <p style={{ fontSize: 10, color: "#6b7280", marginTop: 6, fontStyle: "italic" }}>The goat can&apos;t chew fog.</p>
              </div>
            )}
          </section>

{/* ── Active Tracks ── */}
          <section>
            {signalWarning && (
              <div style={{ marginBottom: 12, padding: "10px 14px", borderRadius: 8, background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)" }}>
                <p style={{ fontSize: 12, color: "#f59e0b" }}>⚠️ {signalWarning}</p>
              </div>
            )}
            <div className="flex items-center gap-2 mb-3">
              <Image src="/icons/icon_tracks.webp" alt="" width={20} height={20} />
              <h2 className="font-syne text-goat-white font-bold" style={{ fontSize: 18 }}>
                Active Tracks
              </h2>
              {signals.length > 0 && (
                <span style={{
                  fontSize: 11, color: "#a78bfa", background: "rgba(97,0,255,0.15)",
                  border: "1px solid rgba(97,0,255,0.3)", borderRadius: 99, padding: "2px 8px",
                }}>
                  {signals.length}
                </span>
              )}
            </div>

            {signalsLoading ? (
              <div className="flex items-center justify-center py-12">
                <p style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.15em" }}>
                  Loading tracks…
                </p>
              </div>
            ) : signals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 gap-4">
                <Image src="/icons/goatflow_logo_nobg.webp" alt="GOATflow" width={72} height={72} style={{ opacity: 0.3 }} />
                <p style={{ fontSize: 13, color: "#6b7280", textAlign: "center" }}>The pasture is clear.</p>
                <p style={{ fontSize: 11, color: "#4b5563", textAlign: "center" }}>
                  Use the Track Sieve above to generate your next set of tracks.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {signals.map((signal, i) => (
                  <TrackCard
                    key={signal.id}
                    signal={signal}
                    index={i}
                    onComplete={complete}
                    onCancel={cancel}
                    onCompleted={(result) => handleTrackCompleted(result, signal.created_at)}
                    onCancelled={handleTrackCancelled}
                  />
                ))}
              </div>
            )}
          </section>
      </div>
    </div>
  );
}
