import { api } from "./client";
import type { OperationalLogEntry } from "../types";

export type LogFilter = "all" | "completed" | "dismissed" | "reordered";

export async function getLog(filter: LogFilter = "all"): Promise<OperationalLogEntry[]> {
  const res = await api.get<OperationalLogEntry[]>("/log", {
    params: { filter },
  });
  return res.data;
}
