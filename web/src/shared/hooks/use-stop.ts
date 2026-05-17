"use client";

import { fetchStop } from "@/shared/api/stop";
import type { Stop } from "@/shared/api/stops";
import { useQuery } from "@tanstack/react-query";

export const useStop = (
  stopId: string,
): { data: Stop | null | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<Stop | null>({
    queryKey: ["stop", stopId],
    queryFn: ({ signal }) => fetchStop(stopId, { signal }),
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
