import { api } from "./client";
import type { User, AuthResponse } from "../types";

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>("/auth/login", { username, password });
  return res.data;
}

export async function signup(
  username: string,
  password: string,
  displayName: string
): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>("/auth/signup", {
    username,
    password,
    display_name: displayName,
  });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await api.get<User>("/auth/me");
  return res.data;
}
