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

export const BLEAT_TYPES = [
  { key: "on_fire",         label: "🔥 You on fire today?",   desc: "Check in on their momentum" },
  { key: "how_climbing",    label: "🏔️ How's the climb?",     desc: "General progress check" },
  { key: "stack_hay",       label: "🧀 Stack that Hay!",       desc: "Encouragement" },
  { key: "summit_incoming", label: "⚡ Summit incoming?",      desc: "Nudge toward completion" },
  { key: "holding_fence",   label: "🛡️ Holding the fence?",   desc: "Streak accountability" },
  { key: "goat_move",       label: "🐐 GOAT move incoming?",  desc: "Hype them up" },
];

export interface Bleat {
  id: number;
  herd_id: number;
  sender_id: string;
  recipient_id: string;
  bleat_type: string;
  message: string | null;
  responded_at: string | null;
  response_hay_earned: number;
  response_type: string | null;
  response_text: string | null;
  response_hay_tier: string | null;
  created_at: string;
  sender_name?: string;
  recipient_name?: string;
}

export interface BleatStats {
  total_received: number;
  total_responded: number;
  total_sent: number;
  response_rate: number;
  avg_response_hours: number | null;
  avg_hay_per_response: number | null;
}

export async function sendBleat(recipient_id: string, bleat_type: string): Promise<Bleat> {
  const res = await api.post<Bleat>("/herds/bleats/send", { recipient_id, bleat_type });
  return res.data;
}

export async function getBleats(): Promise<{ received: Bleat[]; sent: Bleat[] }> {
  const res = await api.get<{ received: Bleat[]; sent: Bleat[] }>("/herds/bleats");
  return res.data;
}

export async function respondBleat(
  bleat_id: number,
  response_type: string,
  response_text?: string,
): Promise<{ hay_earned: number; speed_label: string; response_type: string; message: string }> {
  const res = await api.post(`/herds/bleats/${bleat_id}/respond`, { response_type, response_text });
  return res.data;
}

export async function getBleatStats(): Promise<BleatStats> {
  const res = await api.get<BleatStats>("/herds/bleats/stats");
  return res.data;
}
