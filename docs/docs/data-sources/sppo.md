---
sidebar_position: 1
---

# SPPO (RJ-SMTR)

The real-time GPS feed for Rio de Janeiro buses and BRT. Provided by RJ-SMTR (Secretaria Municipal de Transportes) under the data.rio open data initiative. Documented from a live spike on 2026-05-09 — see `vambora/spike/` and `plan.md` "Appendix: SPPO API Quirks".

## Endpoint

```
GET https://dados.mobilidade.rio/gps/sppo
```

No authentication required.

## Required query params

| Param | Format | Notes |
|---|---|---|
| `dataInicial` | `YYYY-MM-DD HH:MM:SS` (BRT, UTC-3) | Filters by `datahoraenvio` (server arrival), not `datahora` |
| `dataFinal`   | same | |

The unfiltered response is ~90 MB and effectively unusable. With a 30-second window the response shrinks to ~750 KB (~1500 records, ~1100 unique vehicles, ~310 lines).

`DD-MM-YYYY` formats silently return `[]`. Be specific.

## Per-record JSON shape

```json
{
  "ordem": "B11622",
  "linha": "363",
  "latitude": "-22,89623",
  "longitude": "-43,35265",
  "datahora": "1778261830000",
  "datahoraenvio": "1778261843000",
  "datahoraservidor": "1778261874000",
  "velocidade": "0"
}
```

| Field | Mapping | Notes |
|---|---|---|
| `ordem` | `vehicle_id` | |
| `linha` | `line_id` | Heterogeneous: `007`, `292`, `SV669`, `LECD147`, `2345`, `GARAGEM` |
| `latitude` / `longitude` | `coordinate` | **Comma decimal** strings; coerce to float |
| `datahora` | `recorded_at` | ms-since-epoch as string |
| `datahoraenvio` | `sent_at` | ms-since-epoch as string |
| `datahoraservidor` | `received_at` | ms-since-epoch as string |
| `velocidade` | `speed_kmh` | Integer string, km/h |

There is **no** `heading` field.

## Response quirks

- **Content-Type lies**: `text/html; charset=utf-8` even though the body is JSON. `httpx.Response.json()` parses it because it doesn't enforce the header; stricter clients need an override.
- **Stale fixes inside fresh windows**: the date-range filter operates on `datahoraenvio`, so a "fresh" 30-second window can include GPS fixes whose `datahora` is hours old. **Always gate liveness checks on `received_at`, not `recorded_at`.**
- **Intra-window overlap**: ~2 % of records in fetch N are duplicates of records in fetch N-1 (same `ordem` + `datahora`). The `(vehicle_id, recorded_at)` UNIQUE + `ON CONFLICT DO NOTHING` upsert pattern handles this cleanly.
- **`linha` includes non-route values**: `GARAGEM` indicates a bus parked at the depot. The `catalog` context normalization layer should tag these as service-only, not regular routes.

## Adapter

Implemented in `vambora-backend/src/vambora/adapters/outbound/providers/sppo_client.py`. Pydantic v2 model handles the comma-decimal and ms-epoch coercions defensively; malformed rows are skipped and counted, never crash the poll.
