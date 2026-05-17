"use client";

import { fetchVehicles } from "@/shared/api/client";
import type { VehiclePosition } from "@/shared/api/types";
import { useQuery } from "@tanstack/react-query";

const REFRESH_MS = 15_000;

export const useLiveVehicles = (
  lineId?: string,
): { data: VehiclePosition[] | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<VehiclePosition[]>({
    queryKey: ["vehicles", { lineId }],
    queryFn: ({ signal }) => fetchVehicles({ freshSeconds: 180, lineId, signal }),
    refetchInterval: REFRESH_MS,
    staleTime: REFRESH_MS,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
