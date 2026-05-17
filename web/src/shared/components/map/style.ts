import type { StyleSpecification } from "maplibre-gl";

// Carto's free dark basemap. No API key required. Production should swap to
// self-hosted Protomaps (PMTiles on Cloudflare R2) or MapTiler — see
// plan.md "Tech Stack > Web > Map" and ADRs.
// OSM's tile.openstreetmap.org blocks direct browser usage by policy
// (operations.osmfoundation.org/policies/tiles/), so we don't use it here.
export const DEV_BASEMAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors © CARTO",
    },
  },
  layers: [{ id: "basemap", type: "raster", source: "carto" }],
};
