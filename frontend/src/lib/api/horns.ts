import { api } from "./client";
import type { Horn } from "../types";

export async function getHorns(): Promise<Horn[]> {
  const res = await api.get<{ rules: Horn[] }>("/horns");
  return res.data?.rules ?? [];
}

export async function saveHorns(rules: Horn[]): Promise<{ rules: Horn[] }> {
  const res = await api.put<{ rules: Horn[] }>("/horns", { rules });
  return res.data;
}
