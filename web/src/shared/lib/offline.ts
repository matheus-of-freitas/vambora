"use client";

import type { LineRealtime } from "@/shared/api/line-realtime";
import type { Stop } from "@/shared/api/stops";
import { getBundle } from "@/shared/storage/bundle";

// A network read failed. AbortError is real cancellation (component unmount,
// query superseded) and must propagate; anything else means "offline" and we
// try the stored bundle.
export const isAbort = (err: unknown): boolean =>
  err instanceof DOMException && err.name === "AbortError";

const haversineM = (aLat: number, aLon: number, bLat: number, bLon: number): number => {
  const R = 6_371_000;
  const dLat = ((bLat - aLat) * Math.PI) / 180;
  const dLon = ((bLon - aLon) * Math.PI) / 180;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((aLat * Math.PI) / 180) * Math.cos((bLat * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
};

export const offlineStop = async (stopId: string): Promise<Stop | null> => {
  const bundle = await getBundle();
  const s = bundle?.stops.find((x) => x.stop_id === stopId);
  if (!s) return null;
  return {
    stop_id: s.stop_id,
    code: s.code,
    name: s.name,
    latitude: s.lat,
    longitude: s.lon,
    parent_station: null,
    wheelchair_boarding: null,
  };
};

export const offlineNearbyStops = async (
  lat: number,
  lon: number,
  radiusM: number,
  limit: number,
): Promise<Stop[]> => {
  const bundle = await getBundle();
  if (!bundle) return [];
  return bundle.stops
    .map((s) => ({ s, d: haversineM(lat, lon, s.lat, s.lon) }))
    .filter((x) => x.d <= radiusM)
    .sort((a, b) => a.d - b.d)
    .slice(0, limit)
    .map(({ s }) => ({
      stop_id: s.stop_id,
      code: s.code,
      name: s.name,
      latitude: s.lat,
      longitude: s.lon,
      parent_station: null,
      wheelchair_boarding: null,
    }));
};

export const offlineLineRealtime = async (shortName: string): Promise<LineRealtime | null> => {
  const bundle = await getBundle();
  const routes = (bundle?.routes ?? []).filter((r) => r.short_name === shortName);
  if (routes.length === 0) return null;
  return {
    // Offline: no live vehicles. agency_id/route_type/text_color aren't used
    // by the line view; safe defaults keep the type honest.
    routes: routes.map((r) => ({
      route_id: r.route_id,
      agency_id: "",
      short_name: r.short_name,
      long_name: r.long_name,
      route_type: 700,
      color: r.color,
      text_color: null,
    })),
    vehicles: [],
  };
};

export interface OfflineStopLine {
  short_name: string;
  headway_minutes: number | null;
}

export const offlineStopLines = async (stopId: string): Promise<OfflineStopLine[]> => {
  const bundle = await getBundle();
  if (!bundle) return [];
  const lines = bundle.stop_lines[stopId] ?? [];
  return lines.map((short_name) => {
    const secs = bundle.headways[short_name];
    return {
      short_name,
      headway_minutes: secs ? Math.max(1, Math.round(secs / 60)) : null,
    };
  });
};
