import { api } from "./client";
import type { Signal } from "../types";

export async function runChurn(
  files: File[],
  text: string
): Promise<Signal[]> {
  const form = new FormData();
  form.append("text", text);
  for (const file of files) {
    form.append("files", file, file.name);
  }
  const res = await api.post<Signal[]>("/churn", form, {
    headers: { "Content-Type": undefined },
  });
  return res.data;
}
