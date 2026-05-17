"use client";

import { useEffect, useState } from "react";

const BRT_OFFSET_MIN = -180; // UTC-3, no DST in Brazil since 2019.

const secondsSinceMidnightBRT = (): number => {
  // Date.getTime() is always UTC ms; we just shift by the BRT offset and
  // read UTC components of that virtual moment to get BRT wall time. Works
  // regardless of where the browser is.
  const brt = new Date(Date.now() + BRT_OFFSET_MIN * 60_000);
  return brt.getUTCHours() * 3600 + brt.getUTCMinutes() * 60 + brt.getUTCSeconds();
};

/**
 * Reactive seconds-since-midnight in BRT, refreshed every ``intervalMs``.
 * Used to render relative arrival times like "em 4 min".
 */
export const useNowSecondsBRT = (intervalMs = 30_000): number => {
  const [now, setNow] = useState(() => secondsSinceMidnightBRT());
  useEffect(() => {
    const id = setInterval(() => setNow(secondsSinceMidnightBRT()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
};
