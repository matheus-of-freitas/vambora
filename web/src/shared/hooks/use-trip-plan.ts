"use client";

import { type Itinerary, type PlanTripRequest, planTrip } from "@/shared/api/trip-plan";
import { useQuery } from "@tanstack/react-query";

// Triggered, not reactive: the query stays disabled until the user submits a
// request. Passing a fresh `request` object (new reference) re-runs the plan.
export const useTripPlan = (
  request: PlanTripRequest | null,
): {
  data: Itinerary[] | undefined;
  isFetching: boolean;
  error: unknown;
} => {
  const query = useQuery<Itinerary[]>({
    queryKey: ["trip-plan", request],
    queryFn: ({ signal }) => planTrip(request as PlanTripRequest, { signal }),
    enabled: request !== null,
    staleTime: 30 * 1000,
    retry: false,
  });
  return { data: query.data, isFetching: query.isFetching, error: query.error };
};
