"use client";

import { type ScheduledArrival, fetchStopArrivals } from "@/shared/api/stop-arrivals";
import { useQuery } from "@tanstack/react-query";

export const useStopArrivals = (
  stopId: string,
  limit = 10,
): { data: ScheduledArrival[] | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<ScheduledArrival[]>({
    queryKey: ["stop-arrivals", stopId, limit],
    queryFn: ({ signal }) => fetchStopArrivals(stopId, { limit, signal }),
    refetchInterval: 30_000,
    staleTime: 30_000,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
