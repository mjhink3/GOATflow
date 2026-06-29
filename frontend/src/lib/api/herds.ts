import { api } from "./client";

export interface HerdMember {
  user_id: string;
  display_name: string;
  role: "member" | "herdboss";
  joined_at?: string;
  total_hay_earned: number | null;
  hay: number | null;
  tasks_completed: number | null;
  level: number | null;
  fresh_cheese: number | null;
}

export interface Herd {
  id: number;
  name: string;
  description: string | null;
  pasture_level: number;
  herd_title: string;
  created_by: string;
  created_at: string;
}

export interface HerdData {
  herd: Herd | null;
  members: HerdMember[];
  stats: Record<string, number> | null;
  invite_code: string | null;
  my_role: "member" | "herdboss";
}

export async function getMyHerd(): Promise<HerdData> {
  const res = await api.get<HerdData>("/herds/mine");
  return res.data;
}

export async function createHerd(
  name: string,
  description?: string,
): Promise<{ herd: Herd; invite_code: string }> {
  const res = await api.post("/herds/", { name, description });
  return res.data;
}

export async function joinHerd(
  invite_code: string,
): Promise<{ herd: Herd; role: string }> {
  const res = await api.post("/herds/join", { invite_code });
  return res.data;
}

export async function leaveHerd(): Promise<void> {
  await api.post("/herds/leave");
}

export async function generateInvite(): Promise<{ invite_code: string }> {
  const res = await api.post("/herds/invite/generate");
  return res.data;
}

export async function getHerdLeaderboard(): Promise<HerdMember[]> {
  const res = await api.get<HerdMember[]>("/herds/leaderboard");
  return res.data;
}
