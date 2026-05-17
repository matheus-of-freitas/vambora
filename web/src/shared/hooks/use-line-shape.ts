"use client";

import { type ShapeFeatureCollection, fetchLineShape } from "@/shared/api/line-shape";
import { useQuery } from "@tanstack/react-query";

export const useLineShape = (
  shortName: string,
): {
  data: ShapeFeatureCollection | null | undefined;
  isLoading: boolean;
  error: unknown;
} => {
  const query = useQuery<ShapeFeatureCollection | null>({
    queryKey: ["line-shape", shortName],
    queryFn: ({ signal }) => fetchLineShape(shortName, { signal }),
    staleTime: 60 * 60 * 1000, // shapes change only at GTFS import time
    refetchOnWindowFocus: false,
  });
  return { data: query.data, isLoading: query.isLoading, error: query.error };
};
