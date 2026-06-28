"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getPlayer } from "@/lib/api/player";
import type { Player } from "@/lib/types";

export function usePlayer() {
  const qc = useQueryClient();

  const { data: player, isLoading, refetch } = useQuery<Player>({
    queryKey: ["player"],
    queryFn: getPlayer,
    staleTime: 60_000,
  });

  function invalidate() {
    qc.invalidateQueries({ queryKey: ["player"] });
  }

  return { player, isLoading, refetch, invalidate };
}
