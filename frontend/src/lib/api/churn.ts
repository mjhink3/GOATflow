import { api } from "./client";
import type { Signal } from "../types";

export interface ChurnResponse {
  signals: Signal[];
  rejected_inputs: string[];
  signal_warning: string;
}

export async function runChurn(
  files: File[],
  text: string
): Promise<ChurnResponse> {
  const form = new FormData();
  form.append("text", text);
  for (const file of files) {
    form.append("files", file, file.name);
  }
  const res = await api.post<ChurnResponse>("/churn", form, {
    headers: { "Content-Type": undefined },
  });
  return res.data;
}
