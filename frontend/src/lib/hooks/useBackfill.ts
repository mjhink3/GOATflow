"use client";
import { useEffect } from "react";
import { backfillFromLocalStorage } from "@/lib/api/behavioral";
import { useAuth } from "./useAuth";

export function useBackfill() {
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) return;
    if (localStorage.getItem("goatflow_backfill_done")) return;

    const trailNotesRaw = localStorage.getItem("goatflow_trail_notes");
    const gutChecksRaw = localStorage.getItem("goatflow_track_ratings");
    const cancelReasonsRaw = localStorage.getItem("goatflow_cancel_reasons");

    const trailNotes = trailNotesRaw
      ? Object.entries(JSON.parse(trailNotesRaw)).map(([log_id, val]) => ({
          log_id: parseInt(log_id),
          ...(val as Record<string, unknown>),
        }))
      : [];

    const gutChecks = gutChecksRaw
      ? (JSON.parse(gutChecksRaw) as Record<string, unknown>[])
      : [];

    const cancelReasons = cancelReasonsRaw
      ? Object.entries(JSON.parse(cancelReasonsRaw)).map(([log_id, val]) => ({
          log_id: parseInt(log_id),
          ...(val as Record<string, unknown>),
        }))
      : [];

    if (trailNotes.length === 0 && gutChecks.length === 0 && cancelReasons.length === 0) {
      localStorage.setItem("goatflow_backfill_done", "true");
      return;
    }

    backfillFromLocalStorage({
      trail_notes: trailNotes,
      gut_checks: gutChecks,
      cancel_reasons: cancelReasons,
      achievements: [],
    }).then(result => {
      if (result) {
        console.log("[backfill] complete:", result);
        localStorage.setItem("goatflow_backfill_done", "true");
      }
    });
  }, [isAuthenticated]);
}
