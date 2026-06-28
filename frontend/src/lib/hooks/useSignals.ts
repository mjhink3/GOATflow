"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSignals, completeSignal as apiComplete, cancelSignal as apiCancel } from "@/lib/api/signals";
import type { Signal } from "@/lib/types";

export function useSignals() {
  const qc = useQueryClient();

  const { data: signals = [], isLoading, refetch } = useQuery({
    queryKey: ["signals"],
    queryFn: getSignals,
    staleTime: 30_000,
  });

  const completeMutation = useMutation({
    mutationFn: ({ id, timeEstimateMinutes }: { id: number; timeEstimateMinutes?: number }) =>
      apiComplete(id, timeEstimateMinutes),
    onMutate: async ({ id }) => {
      await qc.cancelQueries({ queryKey: ["signals"] });
      const prev = qc.getQueryData<Signal[]>(["signals"]);
      qc.setQueryData<Signal[]>(["signals"], (old) => (old ?? []).filter((s) => s.id !== id));
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(["signals"], ctx.prev);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["signals"] });
      qc.invalidateQueries({ queryKey: ["player"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => apiCancel(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["signals"] });
      const prev = qc.getQueryData<Signal[]>(["signals"]);
      qc.setQueryData<Signal[]>(["signals"], (old) => (old ?? []).filter((s) => s.id !== id));
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(["signals"], ctx.prev);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["signals"] });
    },
  });

  return {
    signals,
    isLoading,
    refetch,
    complete: (id: number, timeEstimateMinutes?: number) =>
      completeMutation.mutateAsync({ id, timeEstimateMinutes }),
    cancel: (id: number) => cancelMutation.mutateAsync(id),
    isCompleting: completeMutation.isPending,
    isCancelling: cancelMutation.isPending,
  };
}
