"use client";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import { ROUTE_COLORS } from "./route-colors";
import { DEV_BASEMAP_STYLE } from "./style";

interface Props {
  longitude: number;
  latitude: number;
}

export const SingleStopMap = ({ longitude, latitude }: Props) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const styleOverride = process.env.NEXT_PUBLIC_MAP_STYLE;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleOverride && styleOverride !== "" ? styleOverride : DEV_BASEMAP_STYLE,
      center: [longitude, latitude],
      zoom: 16,
      attributionControl: { compact: true },
    });
    map.on("load", () => {
      map.addSource("stop", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              geometry: { type: "Point", coordinates: [longitude, latitude] },
              properties: {},
            },
          ],
        },
      });
      map.addLayer({
        id: "stop-fill",
        type: "circle",
        source: "stop",
        paint: {
          "circle-radius": 8,
          "circle-color": ROUTE_COLORS.vlt,
          "circle-stroke-width": 2,
          "circle-stroke-color": "rgba(0,0,0,0.6)",
        },
      });
      map.addLayer({
        id: "stop-halo",
        type: "circle",
        source: "stop",
        paint: {
          "circle-radius": 18,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 2,
          "circle-stroke-color": ROUTE_COLORS.vlt,
          "circle-stroke-opacity": 0.6,
        },
      });
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [longitude, latitude]);

  return <div ref={containerRef} className="h-full w-full" />;
};
