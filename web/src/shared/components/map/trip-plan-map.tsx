"use client";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import type { Itinerary } from "@/shared/api/trip-plan";
import { ROUTE_COLORS } from "./route-colors";
import { DEV_BASEMAP_STYLE } from "./style";

interface Props {
  itinerary: Itinerary | null;
}

const RIO_CENTER: [number, number] = [-43.1825, -22.9068];

const transitColor = (mode: string): string => {
  switch (mode) {
    case "BUS":
      return ROUTE_COLORS.bus;
    case "RAIL":
    case "SUBWAY":
      return ROUTE_COLORS.brt;
    case "TRAM":
    case "FERRY":
      return ROUTE_COLORS.vlt;
    default:
      return ROUTE_COLORS.bus;
  }
};

type LineFeature = GeoJSON.Feature<GeoJSON.LineString, { color: string }>;

const toFeatures = (itinerary: Itinerary | null) => {
  const walk: LineFeature[] = [];
  const transit: LineFeature[] = [];
  if (!itinerary) return { walk, transit };
  for (const leg of itinerary.legs) {
    if (leg.geometry.length < 2) continue;
    const feature: LineFeature = {
      type: "Feature",
      geometry: { type: "LineString", coordinates: leg.geometry },
      properties: { color: leg.mode === "WALK" ? ROUTE_COLORS.walk : transitColor(leg.mode) },
    };
    (leg.mode === "WALK" ? walk : transit).push(feature);
  }
  return { walk, transit };
};

const endpointFeatures = (itinerary: Itinerary | null): GeoJSON.FeatureCollection => {
  if (!itinerary || itinerary.legs.length === 0) {
    return { type: "FeatureCollection", features: [] };
  }
  const first = itinerary.legs[0];
  const last = itinerary.legs[itinerary.legs.length - 1];
  if (!first || !last) return { type: "FeatureCollection", features: [] };
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [first.from_lon, first.from_lat] },
        properties: { role: "origin" },
      },
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [last.to_lon, last.to_lat] },
        properties: { role: "destination" },
      },
    ],
  };
};

export const TripPlanMap = ({ itinerary }: Props) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  // The mount effect creates the map once and must not depend on `itinerary`;
  // it reads the latest value through this ref instead.
  const itineraryRef = useRef(itinerary);
  const readyRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const styleOverride = process.env.NEXT_PUBLIC_MAP_STYLE;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleOverride && styleOverride !== "" ? styleOverride : DEV_BASEMAP_STYLE,
      center: RIO_CENTER,
      zoom: 11,
      attributionControl: { compact: true },
    });
    map.on("load", () => {
      const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
      map.addSource("walk", { type: "geojson", data: empty });
      map.addSource("transit", { type: "geojson", data: empty });
      map.addSource("endpoints", { type: "geojson", data: empty });
      map.addLayer({
        id: "walk-line",
        type: "line",
        source: "walk",
        paint: {
          "line-color": ["get", "color"],
          "line-width": 4,
          "line-dasharray": [1, 2],
        },
      });
      map.addLayer({
        id: "transit-line",
        type: "line",
        source: "transit",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": ["get", "color"], "line-width": 5 },
      });
      map.addLayer({
        id: "endpoint-dot",
        type: "circle",
        source: "endpoints",
        paint: {
          "circle-radius": 7,
          "circle-color": ["match", ["get", "role"], "origin", ROUTE_COLORS.vlt, ROUTE_COLORS.bus],
          "circle-stroke-width": 2,
          "circle-stroke-color": "rgba(0,0,0,0.6)",
        },
      });
      mapRef.current = map;
      readyRef.current = true;
      applyItinerary(map, itineraryRef.current);
    });
    return () => {
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
    };
  }, []);

  useEffect(() => {
    itineraryRef.current = itinerary;
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    applyItinerary(map, itinerary);
  }, [itinerary]);

  return <div ref={containerRef} className="h-full w-full" />;
};

const applyItinerary = (map: MapLibreMap, itinerary: Itinerary | null) => {
  const { walk, transit } = toFeatures(itinerary);
  (map.getSource("walk") as maplibregl.GeoJSONSource | undefined)?.setData({
    type: "FeatureCollection",
    features: walk,
  });
  (map.getSource("transit") as maplibregl.GeoJSONSource | undefined)?.setData({
    type: "FeatureCollection",
    features: transit,
  });
  (map.getSource("endpoints") as maplibregl.GeoJSONSource | undefined)?.setData(
    endpointFeatures(itinerary),
  );

  const coords = [...walk, ...transit].flatMap((f) => f.geometry.coordinates);
  if (coords.length === 0) return;
  const bounds = coords.reduce(
    (b, c) => b.extend(c as [number, number]),
    new maplibregl.LngLatBounds(coords[0] as [number, number], coords[0] as [number, number]),
  );
  map.fitBounds(bounds, { padding: 60, maxZoom: 15, duration: 600 });
};
