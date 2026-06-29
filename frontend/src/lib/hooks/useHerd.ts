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

  const refetchHerd = async () => {
    await qc.invalidateQueries({ queryKey: ["herd"] });
    await qc.refetchQueries({ queryKey: ["herd"] });
  };

  const create = useMutation({
    mutationFn: ({
      name,
      description,
      herd_type,
      work_domain,
    }: {
      name: string;
      description?: string;
      herd_type?: "free_range" | "work";
      work_domain?: string;
    }) => createHerd(name, description, herd_type ?? "free_range", work_domain),
    onSuccess: refetchHerd,
  });

  const join = useMutation({
    mutationFn: (invite_code: string) => joinHerd(invite_code),
    onSuccess: refetchHerd,
  });

  const leave = useMutation({
    mutationFn: leaveHerd,
    onSuccess: refetchHerd,
  });

  const newInvite = useMutation({
    mutationFn: generateInvite,
    onSuccess: refetchHerd,
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
