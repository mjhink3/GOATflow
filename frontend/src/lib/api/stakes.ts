import { api } from "./client";
import type { Stake } from "../types";

export async function getTodayStake(): Promise<Stake | null> {
  const res = await api.get<Stake | null>("/stakes/today");
  return res.data;
}

export async function getYesterdayStake(): Promise<Stake | null> {
  const res = await api.get<Stake | null>("/stakes/yesterday");
  return res.data;
}

export async function createStake(text: string): Promise<Stake> {
  const res = await api.post<Stake>("/stakes", { stake_text: text });
  return res.data;
}

export async function claimStake(): Promise<{ hay_earned: number; message: string }> {
  const res = await api.post("/stakes/claim");
  return res.data;
}

export async function breakStake(): Promise<{ message: string }> {
  const res = await api.post("/stakes/break");
  return res.data;
}
