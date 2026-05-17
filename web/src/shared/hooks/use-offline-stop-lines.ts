"use client";

import { useEffect, useState } from "react";

import { type OfflineStopLine, offlineStopLines } from "@/shared/lib/offline";

// Lines serving a stop, sourced from the downloaded bundle (stop_lines +
// headways). The offline substitute for the schedule.
export const useOfflineStopLines = (stopId: string): OfflineStopLine[] => {
  const [lines, setLines] = useState<OfflineStopLine[]>([]);

  useEffect(() => {
    let active = true;
    offlineStopLines(stopId)
      .then((l) => active && setLines(l))
      .catch(() => active && setLines([]));
    return () => {
      active = false;
    };
  }, [stopId]);

  return lines;
};
