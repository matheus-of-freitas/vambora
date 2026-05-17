"use client";

import { type ArrivalPrediction, fetchStopPredictions } from "@/shared/api/stop-predictions";
import { useQuery } from "@tanstack/react-query";

// Naive real-time ETAs. Polls faster than scheduled arrivals since the
// underlying SPPO positions move; empty result -> fall back to schedule.
export const useStopPredictions = (
  stopId: string,
  limit = 10,
): { data: ArrivalPrediction[] | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<ArrivalPrediction[]>({
    queryKey: ["stop-predictions", stopId, limit],
    queryFn: ({ signal }) => fetchStopPredictions(stopId, { limit, signal }),
    refetchInterval: 20_000,
    staleTime: 15_000,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
