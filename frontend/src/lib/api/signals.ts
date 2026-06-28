import { api } from "./client";
import type { Signal, CompletionResult } from "../types";

export async function getSignals(): Promise<Signal[]> {
  const res = await api.get<Signal[]>("/signals");
  return res.data;
}

export async function completeSignal(
  id: number,
  timeEstimateMinutes?: number
): Promise<CompletionResult> {
  const res = await api.post<CompletionResult>(`/signals/${id}/complete`, {
    time_estimate_minutes: timeEstimateMinutes ?? null,
  });
  return res.data;
}

export async function cancelSignal(id: number): Promise<{ ok: boolean; log_id: number | null; task_name: string }> {
  const res = await api.post(`/signals/${id}/cancel`);
  return res.data;
}
