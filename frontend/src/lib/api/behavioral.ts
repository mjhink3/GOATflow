import { api } from "./client";

export async function saveTrailNote(data: {
  log_id?: number | null;
  task_name: string;
  question?: string;
  note?: string;
}) {
  try {
    await api.post("/behavioral/trail-notes", data);
  } catch (err) {
    console.error("[behavioral] saveTrailNote failed:", err);
  }
}

export async function saveGutCheck(data: {
  log_id?: number | null;
  task_name: string;
  assigned_tier?: string;
  rating: string;
  reason?: string;
}) {
  try {
    await api.post("/behavioral/gut-checks", data);
  } catch (err) {
    console.error("[behavioral] saveGutCheck failed:", err);
  }
}

export async function saveCancelReason(data: {
  log_id?: number | null;
  task_name: string;
  reason?: string;
}) {
  try {
    await api.post("/behavioral/cancel-reasons", data);
  } catch (err) {
    console.error("[behavioral] saveCancelReason failed:", err);
  }
}

export async function unlockAchievement(data: {
  achievement_id: string;
  achievement_name: string;
  tier: number;
}) {
  try {
    await api.post("/behavioral/achievements/unlock", data);
  } catch (err) {
    console.error("[behavioral] unlockAchievement failed:", err);
  }
}

export async function getAchievements(): Promise<Array<{ achievement_id: string; unlocked_at: string }>> {
  try {
    const res = await api.get("/behavioral/achievements");
    return res.data;
  } catch {
    return [];
  }
}

export async function backfillFromLocalStorage(data: {
  trail_notes: Array<Record<string, unknown>>;
  gut_checks: Array<Record<string, unknown>>;
  cancel_reasons: Array<Record<string, unknown>>;
  achievements: Array<Record<string, unknown>>;
}) {
  try {
    const res = await api.post("/behavioral/backfill", data);
    return res.data;
  } catch (err) {
    console.error("[behavioral] backfill failed:", err);
    return null;
  }
}
