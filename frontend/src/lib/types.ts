export interface User {
  id: string;
  username: string;
  display_name: string;
  created_at: string;
}

export interface Player {
  user_id: string;
  level: number;
  total_xp: number;
  total_hay_earned: number;
  hay: number;
  fresh_cheese: number;
  tasks_completed: number;
  onboarding_done: boolean;
  gait_streak: number;
  stake_streak: number;
  streak_shields: number;
  hay_to_next_level: number;
  hay_this_level: number;
  weekly_clip_rate: number | null;
  weekly_clip_rates: number[];
  today_completion_pct: number | null;
  stakes_honor_rate: number | null;
  horn_influence_count: number;
}

export type Difficulty = "Micro" | "Standard" | "High-Leverage" | "GOAT";
export type BleepType = "Summit Call" | "Routine Grazing";
export type Resolution = "completed" | "dismissed" | "cancelled" | "reordered";

export interface Signal {
  id: number;
  task_name: string;
  why: string;
  xp_reward: Difficulty;
  operational_weight: number;
  completed: boolean;
  directive_applied: boolean;
  bleat_type: BleepType;
  created_at: string;
  completed_at: string | null;
  user_id: string;
  horn_applied_name: string;
  category: string;
}

export type Horn = string;

export interface Stake {
  id: number;
  user_id: string;
  stake_text: string;
  date: string;
  status: "active" | "claimed" | "broken" | "pending";
  hay_earned: number;
  created_at: string;
  updated_at: string;
}

export interface OperationalLogEntry {
  id: number;
  user_id: string;
  task_name: string;
  task_why: string;
  resolution: Resolution;
  horn_applied_name: string;
  priority_score: number;
  xp_tier: Difficulty;
  resolved_at: string;
  category: string;
  logged_at: string | null;
  hay_earned: number;
}

export interface CompletionResult {
  task_name: string;
  xp_tier: string;
  hay_earned: number;
  speed_bonus: number;
  difficulty_multiplier: number;
  cheese_gained: number;
  hay_balance: number;
  cheese_total: number;
  leveled_up: boolean;
  new_level: number;
  pasture_name: string;
  log_id?: number;
}

export interface ChurnOutput {
  signals: Signal[];
  message?: string;
}

export interface PlayerStats {
  level: number;
  pasture: string;
  hay_this_level: number;
  hay_to_next_level: number;
  total_hay_earned: number;
  hay: number;
  fresh_cheese: number;
  tasks_completed: number;
  gait_streak: number;
  weekly_clip_rate: number | null;
}

export interface WeeklyClipRate {
  rate: number;
  completed: number;
  total: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  display_name: string;
}
