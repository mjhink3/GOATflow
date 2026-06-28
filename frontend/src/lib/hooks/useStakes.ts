"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTodayStake,
  getYesterdayStake,
  createStake as apiCreate,
  claimStake as apiClaim,
  breakStake as apiBreak,
} from "@/lib/api/stakes";
import type { Stake } from "@/lib/types";

export function useStakes() {
  const qc = useQueryClient();

  const { data: todayStake, isLoading: isLoadingToday } = useQuery<Stake | null>({
    queryKey: ["stakes", "today"],
    queryFn: getTodayStake,
    staleTime: 60_000,
  });

  const { data: yesterdayStake, isLoading: isLoadingYesterday } = useQuery<Stake | null>({
    queryKey: ["stakes", "yesterday"],
    queryFn: getYesterdayStake,
    staleTime: 300_000,
  });

  function invalidateAll() {
    qc.invalidateQueries({ queryKey: ["stakes"] });
    qc.invalidateQueries({ queryKey: ["player"] });
  }

  const createMutation = useMutation({
    mutationFn: (text: string) => apiCreate(text),
    onSuccess: () => invalidateAll(),
  });

  const claimMutation = useMutation({
    mutationFn: apiClaim,
    onSuccess: () => invalidateAll(),
  });

  const breakMutation = useMutation({
    mutationFn: apiBreak,
    onSuccess: () => invalidateAll(),
  });

  return {
    todayStake,
    yesterdayStake,
    isLoadingToday,
    isLoadingYesterday,
    create: (text: string) => createMutation.mutateAsync(text),
    claim: () => claimMutation.mutateAsync(),
    break: () => breakMutation.mutateAsync(),
    isCreating: createMutation.isPending,
    isClaiming: claimMutation.isPending,
    isBreaking: breakMutation.isPending,
  };
}
