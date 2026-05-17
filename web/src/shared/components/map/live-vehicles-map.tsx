"use client";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import type { Stop } from "@/shared/api/stops";
import type { VehiclePosition } from "@/shared/api/types";
import { useLiveVehicles } from "@/shared/hooks/use-live-vehicles";
import { useNearbyStops } from "@/shared/hooks/use-nearby-stops";
import { useVehicleHistory } from "@/shared/hooks/use-vehicle-history";
import { ROUTE_COLORS } from "./route-colors";
import { DEV_BASEMAP_STYLE } from "./style";

const RIO_CENTER: [number, number] = [-43.18, -22.91];
const VEHICLES_SOURCE = "vehicles";
const VEHICLES_LAYER = "vehicles-circle";
const STOPS_SOURCE = "stops";
const STOPS_LAYER = "stops-circle";
const TRAIL_SOURCE = "vehicle-trail";
const TRAIL_LAYER = "vehicle-trail-line";
const TRAIL_HEAD_SOURCE = "vehicle-trail-head";
const TRAIL_HEAD_LAYER = "vehicle-trail-head-circle";

const vehiclesFC = (
  vehicles: ReturnType<typeof useLiveVehicles>["data"] = [],
): GeoJSON.FeatureCollection<GeoJSON.Point> => ({
  type: "FeatureCollection",
  features: (vehicles ?? []).map((v) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [v.longitude, v.latitude] },
    properties: { vehicle_id: v.vehicle_id, line_id: v.line_id, speed_kmh: v.speed_kmh },
  })),
});

const stopsFC = (stops: Stop[] = []): GeoJSON.FeatureCollection<GeoJSON.Point> => ({
  type: "FeatureCollection",
  features: stops.map((s) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
    properties: { stop_id: s.stop_id, name: s.name },
  })),
});

const trailFC = (
  history: VehiclePosition[] = [],
): GeoJSON.FeatureCollection<GeoJSON.LineString> => {
  if (history.length < 2) {
    return { type: "FeatureCollection", features: [] };
  }
  // History is newest-first; trail is older→newer for visual flow.
  const ordered = [...history].reverse();
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: ordered.map((p) => [p.longitude, p.latitude]),
        },
        properties: {},
      },
    ],
  };
};

const trailHeadFC = (history: VehiclePosition[] = []): GeoJSON.FeatureCollection<GeoJSON.Point> => {
  if (history.length === 0) return { type: "FeatureCollection", features: [] };
  const head = history[0]; // newest
  if (!head) return { type: "FeatureCollection", features: [] };
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [head.longitude, head.latitude] },
        properties: { vehicle_id: head.vehicle_id },
      },
    ],
  };
};

interface MapCenter {
  latitude: number;
  longitude: number;
}

interface SelectedVehicle {
  vehicle_id: string;
  line_id: string;
  longitude: number;
  latitude: number;
}

export const LiveVehiclesMap = () => {
  const { data: vehicles } = useLiveVehicles();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

  const [center, setCenter] = useState<MapCenter>({
    latitude: RIO_CENTER[1],
    longitude: RIO_CENTER[0],
  });
  const { data: stops } = useNearbyStops(center, 2000);

  const [selected, setSelected] = useState<SelectedVehicle | null>(null);
  const { data: history } = useVehicleHistory(selected?.vehicle_id ?? null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const styleOverride = process.env.NEXT_PUBLIC_MAP_STYLE;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleOverride && styleOverride !== "" ? styleOverride : DEV_BASEMAP_STYLE,
      center: RIO_CENTER,
      zoom: 13,
      attributionControl: { compact: true },
    });

    // Expose the live map for dev-mode E2E tests. Stripped from production
    // builds via the env guard (Next inlines NODE_ENV at build time).
    if (process.env.NODE_ENV !== "production") {
      (window as unknown as { __VAMBORA_MAP__?: MapLibreMap }).__VAMBORA_MAP__ = map;
    }

    map.on("load", () => {
      map.addSource(STOPS_SOURCE, { type: "geojson", data: stopsFC() });
      map.addLayer({
        id: STOPS_LAYER,
        type: "circle",
        source: STOPS_SOURCE,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 1.5, 15, 4],
          "circle-color": ROUTE_COLORS.vlt,
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(0,0,0,0.5)",
          "circle-opacity": 0.85,
        },
      });

      map.addSource(TRAIL_SOURCE, { type: "geojson", data: trailFC() });
      map.addLayer({
        id: TRAIL_LAYER,
        type: "line",
        source: TRAIL_SOURCE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ROUTE_COLORS.bus,
          "line-width": ["interpolate", ["linear"], ["zoom"], 11, 2, 16, 5],
          "line-opacity": 0.85,
        },
      });

      map.addSource(VEHICLES_SOURCE, { type: "geojson", data: vehiclesFC() });
      map.addLayer({
        id: VEHICLES_LAYER,
        type: "circle",
        source: VEHICLES_SOURCE,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 2, 14, 5],
          "circle-color": ROUTE_COLORS.bus,
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(0,0,0,0.4)",
        },
      });

      map.addSource(TRAIL_HEAD_SOURCE, { type: "geojson", data: trailHeadFC() });
      map.addLayer({
        id: TRAIL_HEAD_LAYER,
        type: "circle",
        source: TRAIL_HEAD_SOURCE,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 6, 16, 12],
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 2,
          "circle-stroke-color": ROUTE_COLORS.bus,
        },
      });
    });

    const onMoveEnd = (): void => {
      const c = map.getCenter();
      setCenter({ latitude: c.lat, longitude: c.lng });
    };
    map.on("moveend", onMoveEnd);

    const onVehicleClick = (e: maplibregl.MapLayerMouseEvent): void => {
      const f = e.features?.[0];
      if (!f) return;
      const props = f.properties ?? {};
      const vehicleId = typeof props.vehicle_id === "string" ? props.vehicle_id : null;
      const lineId = typeof props.line_id === "string" ? props.line_id : "";
      if (!vehicleId) return;
      const geom = f.geometry as GeoJSON.Point;
      setSelected({
        vehicle_id: vehicleId,
        line_id: lineId,
        longitude: geom.coordinates[0] ?? 0,
        latitude: geom.coordinates[1] ?? 0,
      });
    };
    const onVehicleEnter = (): void => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onVehicleLeave = (): void => {
      map.getCanvas().style.cursor = "";
    };
    const onStopClick = (e: maplibregl.MapLayerMouseEvent): void => {
      const f = e.features?.[0];
      if (!f) return;
      const props = f.properties ?? {};
      const stopId = typeof props.stop_id === "string" ? props.stop_id : null;
      const name = typeof props.name === "string" ? props.name : "";
      if (!stopId) return;
      const geom = f.geometry as GeoJSON.Point;
      // Render a stop popup directly via MapLibre — independent of the vehicle
      // selection state.
      popupRef.current?.remove();
      popupRef.current = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: false,
        offset: 12,
        className: "vambora-popup",
      })
        .setLngLat([geom.coordinates[0] ?? 0, geom.coordinates[1] ?? 0])
        .setHTML(stopPopupContent(stopId, name))
        .addTo(map);
      setSelected(null);
    };
    const onStopEnter = (): void => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onStopLeave = (): void => {
      map.getCanvas().style.cursor = "";
    };
    const onBackgroundClick = (e: maplibregl.MapMouseEvent): void => {
      // If the click landed on the vehicles or stops layer, that handler
      // already fired and we leave the popup alone.
      const hits = map.queryRenderedFeatures(e.point, {
        layers: [VEHICLES_LAYER, STOPS_LAYER],
      });
      if (hits.length === 0) setSelected(null);
    };
    map.on("click", VEHICLES_LAYER, onVehicleClick);
    map.on("mouseenter", VEHICLES_LAYER, onVehicleEnter);
    map.on("mouseleave", VEHICLES_LAYER, onVehicleLeave);
    map.on("click", STOPS_LAYER, onStopClick);
    map.on("mouseenter", STOPS_LAYER, onStopEnter);
    map.on("mouseleave", STOPS_LAYER, onStopLeave);
    map.on("click", onBackgroundClick);

    mapRef.current = map;
    return () => {
      map.off("moveend", onMoveEnd);
      map.off("click", VEHICLES_LAYER, onVehicleClick);
      map.off("mouseenter", VEHICLES_LAYER, onVehicleEnter);
      map.off("mouseleave", VEHICLES_LAYER, onVehicleLeave);
      map.off("click", STOPS_LAYER, onStopClick);
      map.off("mouseenter", STOPS_LAYER, onStopEnter);
      map.off("mouseleave", STOPS_LAYER, onStopLeave);
      map.off("click", onBackgroundClick);
      popupRef.current?.remove();
      popupRef.current = null;
      if (process.env.NODE_ENV !== "production") {
        (window as unknown as { __VAMBORA_MAP__?: MapLibreMap }).__VAMBORA_MAP__ = undefined;
      }
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = (): void => {
      const src = map.getSource(VEHICLES_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (src) src.setData(vehiclesFC(vehicles));
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [vehicles]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = (): void => {
      const src = map.getSource(STOPS_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (src) src.setData(stopsFC(stops));
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [stops]);

  // Trail + popup: react to selection + history changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const apply = (): void => {
      const trail = map.getSource(TRAIL_SOURCE) as maplibregl.GeoJSONSource | undefined;
      const head = map.getSource(TRAIL_HEAD_SOURCE) as maplibregl.GeoJSONSource | undefined;
      if (trail) trail.setData(trailFC(history ?? []));
      if (head) head.setData(trailHeadFC(history ?? []));
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);

    if (popupRef.current) {
      popupRef.current.remove();
      popupRef.current = null;
    }
    if (!selected) return;

    const html = popupContent(selected);
    const popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      offset: 12,
      className: "vambora-popup",
    })
      .setLngLat([selected.longitude, selected.latitude])
      .setHTML(html)
      .addTo(map);
    popup.on("close", () => setSelected(null));
    popupRef.current = popup;
  }, [selected, history]);

  return <div ref={containerRef} className="h-full w-full" />;
};

const popupContent = (s: SelectedVehicle): string => {
  const lineLabel = s.line_id || "—";
  const lineHref = s.line_id ? `/lines/${encodeURIComponent(s.line_id)}` : null;
  const linkHtml = lineHref
    ? `<a href="${lineHref}" class="text-primary underline-offset-2 hover:underline">Ver linha ${escapeHtml(lineLabel)}</a>`
    : `<span class="text-muted-foreground">Sem linha</span>`;
  return `
    <div class="space-y-1 p-1 text-sm">
      <div class="font-semibold">${escapeHtml(s.vehicle_id)}</div>
      <div class="text-xs text-muted-foreground">Linha ${escapeHtml(lineLabel)}</div>
      <div class="text-xs">${linkHtml}</div>
    </div>
  `;
};

const stopPopupContent = (stopId: string, name: string): string => `
  <div class="space-y-1 p-1 text-sm">
    <div class="font-semibold">${escapeHtml(name || "Parada")}</div>
    <div class="text-xs text-muted-foreground">${escapeHtml(stopId)}</div>
    <div class="text-xs">
      <a href="/stops/${encodeURIComponent(stopId)}" class="text-primary underline-offset-2 hover:underline">Ver parada</a>
    </div>
  </div>
`;

const escapeHtml = (s: string): string =>
  s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
