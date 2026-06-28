"use client";

import { useState, useEffect, useCallback } from "react";
import { decodeJwt } from "jose";
import { login as apiLogin, signup as apiSignup, getMe } from "@/lib/api/auth";
import type { AuthResponse, User } from "@/lib/types";

const TOKEN_KEY = "goatflow_token";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
    if (!token) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      decodeJwt(token); // throws if malformed / expired signature (not verified here)
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    getMe()
      .then((user) => setState({ user, isAuthenticated: true, isLoading: false }))
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setState({ user: null, isAuthenticated: false, isLoading: false });
      });
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<AuthResponse> => {
    console.log("[useAuth] login() called for:", username);
    const res = await apiLogin(username, password);
    console.log("[useAuth] login() success, storing token, user_id:", res.user_id);
    localStorage.setItem(TOKEN_KEY, res.access_token);
    const user: User = {
      id: res.user_id,
      username: res.username,
      display_name: res.display_name,
      created_at: new Date().toISOString(),
    };
    setState({ user, isAuthenticated: true, isLoading: false });
    return res;
  }, []);

  const signup = useCallback(
    async (username: string, password: string, displayName: string): Promise<AuthResponse> => {
      const res = await apiSignup(username, password, displayName);
      localStorage.setItem(TOKEN_KEY, res.access_token);
      const user: User = {
        id: res.user_id,
        username: res.username,
        display_name: res.display_name,
        created_at: new Date().toISOString(),
      };
      setState({ user, isAuthenticated: true, isLoading: false });
      return res;
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setState({ user: null, isAuthenticated: false, isLoading: false });
    window.location.href = "/login";
  }, []);

  return { ...state, login, logout, signup };
}
