"use client";

import type { VehiclePosition } from "@/shared/api/types";
import { fetchVehicleHistory } from "@/shared/api/vehicle-history";
import { useQuery } from "@tanstack/react-query";

export const useVehicleHistory = (
  vehicleId: string | null,
  limit = 60,
): { data: VehiclePosition[] | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<VehiclePosition[]>({
    queryKey: ["vehicle-history", vehicleId, limit],
    queryFn: ({ signal }) => {
      if (!vehicleId) return Promise.resolve([]);
      return fetchVehicleHistory(vehicleId, { limit, signal });
    },
    enabled: !!vehicleId,
    staleTime: 15_000,
    refetchOnWindowFocus: false,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
