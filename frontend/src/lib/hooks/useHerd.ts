"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMyHerd,
  createHerd,
  joinHerd,
  leaveHerd,
  generateInvite,
} from "@/lib/api/herds";

export function useHerd() {
  const qc = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["herd"],
    queryFn: getMyHerd,
    staleTime: 30_000,
  });

  const create = useMutation({
    mutationFn: ({ name, description }: { name: string; description?: string }) =>
      createHerd(name, description),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["herd"] }),
  });

  const join = useMutation({
    mutationFn: (invite_code: string) => joinHerd(invite_code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["herd"] }),
  });

  const leave = useMutation({
    mutationFn: leaveHerd,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["herd"] }),
  });

  const newInvite = useMutation({
    mutationFn: generateInvite,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["herd"] }),
  });

  return {
    herd: data?.herd ?? null,
    members: data?.members ?? [],
    stats: data?.stats ?? null,
    invite_code: data?.invite_code ?? null,
    my_role: data?.my_role ?? "member",
    isInHerd: !!data?.herd,
    isHerdBoss: data?.my_role === "herdboss",
    isLoading,
    isError,
    create: create.mutateAsync,
    join: join.mutateAsync,
    leave: leave.mutateAsync,
    generateInvite: newInvite.mutateAsync,
  };
}
