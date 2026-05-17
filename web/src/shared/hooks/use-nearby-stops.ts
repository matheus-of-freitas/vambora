"use client";

import { type Stop, fetchNearbyStops } from "@/shared/api/stops";
import { useQuery } from "@tanstack/react-query";

interface Center {
  latitude: number;
  longitude: number;
}

const REFRESH_MS = 60_000;

export const useNearbyStops = (
  center: Center | undefined,
  radiusM = 1500,
): { data: Stop[] | undefined; isLoading: boolean; error: unknown } => {
  const query = useQuery<Stop[]>({
    queryKey: [
      "stops",
      center
        ? {
            lat: Math.round(center.latitude * 1000) / 1000,
            lon: Math.round(center.longitude * 1000) / 1000,
            radiusM,
          }
        : null,
    ],
    queryFn: ({ signal }) => {
      if (!center) return Promise.resolve([]);
      return fetchNearbyStops({
        lat: center.latitude,
        lon: center.longitude,
        radiusM,
        limit: 500,
        signal,
      });
    },
    enabled: !!center,
    staleTime: REFRESH_MS,
    refetchOnWindowFocus: false,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
