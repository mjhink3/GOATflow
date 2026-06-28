"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getHorns, saveHorns as apiSave } from "@/lib/api/horns";
import type { Horn } from "@/lib/types";

export function useHorns() {
  const qc = useQueryClient();

  const { data: horns = [], isLoading } = useQuery<Horn[]>({
    queryKey: ["horns"],
    queryFn: getHorns,
    staleTime: 300_000,
  });

  const saveMutation = useMutation({
    mutationFn: (rules: Horn[]) => apiSave(rules),
    onSuccess: (data) => {
      qc.setQueryData<Horn[]>(["horns"], data.rules);
    },
  });

  return {
    horns,
    isLoading,
    save: (rules: Horn[]) => saveMutation.mutateAsync(rules),
    isSaving: saveMutation.isPending,
  };
}
