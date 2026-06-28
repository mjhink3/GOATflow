import { api } from "./client";
import type { Player } from "../types";

export async function getPlayer(): Promise<Player> {
  const res = await api.get<Player>("/player");
  return res.data;
}
