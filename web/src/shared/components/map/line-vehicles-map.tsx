"use client";

import maplibregl, { type LngLatBoundsLike, type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import type { ShapeFeatureCollection } from "@/shared/api/line-shape";
import type { VehiclePosition } from "@/shared/api/types";
import { ROUTE_COLORS } from "./route-colors";
import { DEV_BASEMAP_STYLE } from "./style";

const RIO_CENTER: [number, number] = [-43.18, -22.91];
const VEHICLES_SOURCE = "line-vehicles";
const VEHICLES_LAYER = "line-vehicles-circle";
const SHAPE_SOURCE = "line-shape";
const SHAPE_LAYER = "line-shape-line";
const EMPTY_SHAPE: ShapeFeatureCollection = { type: "FeatureCollection", features: [] };

const vehiclesFC = (vehicles: VehiclePosition[]): GeoJSON.FeatureCollection<GeoJSON.Point> => ({
  type: "FeatureCollection",
  features: vehicles.map((v) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [v.longitude, v.latitude] },
    properties: { vehicle_id: v.vehicle_id, speed_kmh: v.speed_kmh },
  })),
});

const computeBounds = (
  vehicles: VehiclePosition[],
  shape: ShapeFeatureCollection | null | undefined,
): LngLatBoundsLike | null => {
  let minLat = Number.POSITIVE_INFINITY;
  let maxLat = Number.NEGATIVE_INFINITY;
  let minLon = Number.POSITIVE_INFINITY;
  let maxLon = Number.NEGATIVE_INFINITY;
  let any = false;
  for (const v of vehicles) {
    if (v.latitude < minLat) minLat = v.latitude;
    if (v.latitude > maxLat) maxLat = v.latitude;
    if (v.longitude < minLon) minLon = v.longitude;
    if (v.longitude > maxLon) maxLon = v.longitude;
    any = true;
  }
  if (shape) {
    for (const feat of shape.features) {
      for (const [lon, lat] of feat.geometry.coordinates) {
        if (typeof lat !== "number" || typeof lon !== "number") continue;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
        any = true;
      }
    }
  }
  if (!any) return null;
  return [
    [minLon, minLat],
    [maxLon, maxLat],
  ];
};

interface Props {
  vehicles: VehiclePosition[];
  shape: ShapeFeatureCollection | null | undefined;
  routeColorHex?: string | null;
}

export const LineVehiclesMap = ({ vehicles, shape, routeColorHex }: Props) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const haveFitOnceRef = useRef(false);
  const shapeColor = routeColorHex ? `#${routeColorHex}` : ROUTE_COLORS.bus;
  const shapeColorRef = useRef(shapeColor);
  shapeColorRef.current = shapeColor;

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
      map.addSource(SHAPE_SOURCE, { type: "geojson", data: EMPTY_SHAPE });
      map.addLayer({
        id: SHAPE_LAYER,
        type: "line",
        source: SHAPE_SOURCE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": shapeColorRef.current,
          "line-width": ["interpolate", ["linear"], ["zoom"], 10, 2, 16, 5],
          "line-opacity": 0.85,
        },
      });

      map.addSource(VEHICLES_SOURCE, { type: "geojson", data: vehiclesFC([]) });
      map.addLayer({
        id: VEHICLES_LAYER,
        type: "circle",
        source: VEHICLES_SOURCE,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 4, 14, 8],
          "circle-color": ROUTE_COLORS.bus,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "rgba(0,0,0,0.5)",
        },
      });
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = (): void => {
      const vSrc = map.getSource(VEHICLES_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (vSrc) vSrc.setData(vehiclesFC(vehicles));
      const sSrc = map.getSource(SHAPE_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (sSrc) sSrc.setData(shape ?? EMPTY_SHAPE);
      if (map.getLayer(SHAPE_LAYER)) {
        map.setPaintProperty(SHAPE_LAYER, "line-color", shapeColorRef.current);
      }
      const bounds = computeBounds(vehicles, shape);
      if (bounds && !haveFitOnceRef.current) {
        map.fitBounds(bounds, { padding: 80, maxZoom: 14, duration: 500 });
        haveFitOnceRef.current = true;
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [vehicles, shape]);

  return <div ref={containerRef} className="h-full w-full" />;
};
