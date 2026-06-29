import { api } from "./client";
import type { Horn } from "../types";

export async function getHorns(): Promise<Horn[]> {
  const res = await api.get<{ rules_text: string; horns: Horn[] }>("/horns");
  return res.data?.horns ?? [];
}

export async function saveHorns(rules: Horn[]): Promise<Horn[]> {
  const res = await api.put<{ rules_text: string; horns: Horn[] }>("/horns", {
    rules_text: rules.join("\n"),
  });
  return res.data?.horns ?? [];
}
