import { api } from "./client";

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  value: number;
  user_id: string;
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  current_user_rank: number | null;
  category: string;
}

export async function getLeaderboard(category: string): Promise<LeaderboardResponse> {
  const res = await api.get<LeaderboardResponse>(`/leaderboard/${category}`);
  return res.data;
}
