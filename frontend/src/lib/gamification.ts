import type { Difficulty } from "./types";

// ─── Hay constants ─────────────────────────────────────────────────────────
export const HAY_BASE: Record<Difficulty, number> = {
  Micro:          15,
  Standard:       40,
  "High-Leverage": 100,
  GOAT:           250,
};

export const HAY_SUMMIT_MULT = 1.5;
export const HAY_TO_CHEESE   = 500;
export const BASE_LEVEL_XP   = 500;
export const LEVEL_GROWTH    = 0.20;

// ─── Level math ────────────────────────────────────────────────────────────
export function xp_for_level(level: number): number {
  return Math.ceil(BASE_LEVEL_XP * Math.pow(1 + LEVEL_GROWTH, level - 1));
}

export function compute_level(totalHayEarned: number): { level: number; hayThisLevel: number; hayToNext: number } {
  let level = 1;
  let spent = 0;
  while (true) {
    const needed = xp_for_level(level);
    if (spent + needed > totalHayEarned) {
      return { level, hayThisLevel: totalHayEarned - spent, hayToNext: needed };
    }
    spent += needed;
    level += 1;
  }
}

// ─── Pasture & rank names ───────────────────────────────────────────────────
export const PASTURE_NAMES: Record<number, string> = {
  1: "The Pen",
  2: "The Grazing Grounds",
  3: "The Foothills",
  4: "The Ridgeline",
  5: "The High Cliffs",
  6: "The Summit",
  7: "GOAT Mountain",
};

export const ASCENSION_RANKS: Record<number, string> = {
  1: "The Kid",
  2: "The Starter",
  3: "The Builder",
  4: "The Climber",
  5: "The Leader",
  6: "The Visionary",
  7: "The G.O.A.T.",
};

export function pasture_name(level: number): string {
  return PASTURE_NAMES[Math.min(level, 10)] ?? "The Summit";
}

export function ascension_rank(level: number): string {
  return ASCENSION_RANKS[Math.min(level, 7)] ?? "The G.O.A.T.";
}

// ─── Puns & quotes ─────────────────────────────────────────────────────────
export const GOAT_PUNS: string[] = [
  "You're kidding — in the best way.",
  "Butter believe that was a good one.",
  "You're on a GOAT-streak!",
  "Don't stop me-ow. Wait, wrong animal.",
  "You're absolutely baaad-ass.",
  "Hay, that's what I'm talking about!",
  "Feeling the graze?",
  "That was no bleat feat.",
  "You herd that? Pure productivity.",
  "You're scaling new heights. Literally.",
  "Not to GOAT on about it, but you're crushing it.",
  "Another one bites the cud.",
  "Pasture bedtime, but you're still grinding. GOAT behavior.",
  "No goat, no glory.",
  "GOAT Mode: Activated.",
];

export const HAY_PUNS: string[] = [
  "Hay! That's worth something.",
  "Stack that hay!",
  "The barn is getting full — keep going.",
  "Hay earned, hay stored.",
  "More hay, more levels.",
  "Dry run? No — HAY run.",
  "That Hay isn't gonna stack itself.",
  "Hay while the sun shines.",
  "Field goals only. Hay goals.",
  "One bale at a time.",
  "Hay maker. You.",
  "Certified Hay Hauler.",
  "Bale out? Never. Stack on.",
];

export const FRESH_CHEESE_PUNS: string[] = [
  "Fresh Cheese acquired! The creamery grows.",
  "You've been churning. Now you're earning.",
  "That's the gouda stuff.",
  "Cheesy? No — legendary.",
  "Fresh Cheese: proof you showed up.",
  "Another wheel for the vault.",
  "The cheese stands alone. And so do you.",
  "Aged like fine cheddar. Rewarded like it too.",
  "Brie-lliant work.",
  "You're on a roll. A cheese roll.",
];

export const LEVEL_IMAGES: Record<number, string> = {
  1: "/assets/GOATflow_The_Kid_level_1_1773616494954.webp",
  2: "/assets/GOATflow_The_Starter_level_2_1773616494956.webp",
  3: "/assets/GOATflow_The_Builder_level_3_1773616494949.webp",
  4: "/assets/WorkGOAT_The_Climber_level_4_1773616494957.webp",
  5: "/assets/GOATflow_The_Leader_level_5_1773616494955.webp",
  6: "/assets/GOATflow_The_Visionary_level_6_1773616494957.webp",
  7: "/assets/GOATflow_The_G.O.A.T._level_7_1773616494953.webp",
};

export const GF_QUOTES: string[] = [
  "The summit doesn't come to you. You go to it.",
  "Every trail begins with a single step. Take yours.",
  "Comfort zones are for goats who've given up climbing.",
  "Graze on progress, not perfection.",
  "The mountain doesn't care about your mood. Climb anyway.",
  "Small tracks, big elevation.",
  "Your legacy is built one track at a time.",
  "The herd moves fast. The GOAT moves intentionally.",
  "Summit calls aren't emergencies. They're priorities.",
  "Routine grazing keeps the momentum. Never skip it.",
  "The pasture grows when you show up consistently.",
  "Horns aren't just decoration. They're your compass.",
  "Drop it in the Churn Engine. Let it work.",
  "Hay is proof. Proof is presence.",
  "Fresh Cheese tastes better when you've earned it.",
  "The Pen is just the beginning. The Summit awaits.",
  "Your GAIT Streak is your greatest flex.",
  "GOAT Mountain is built by ordinary days done extraordinarily.",
  "The Bray knows your voice. Trust the process.",
  "Morning Stakes aren't optional for legends.",
  "Trail Notes are your autobiography. Write a good one.",
  "You are not behind. You are exactly where you started your climb.",
  "The Clip Rate doesn't lie. Neither does your effort.",
  "Sieve the noise. Signal the signal.",
  "The Churn Engine sees what you can't. Trust it.",
  "Every goat on this mountain started at The Pen.",
  "Grab life by the horns. Leave the bull behind.",
];
