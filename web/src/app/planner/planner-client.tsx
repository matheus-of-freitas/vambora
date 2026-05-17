"use client";

import Link from "next/link";
import { useState } from "react";

import type { Itinerary, LatLon, PlanTripRequest } from "@/shared/api/trip-plan";
import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { TripPlanMap } from "@/shared/components/map/trip-plan-map";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useTripPlan } from "@/shared/hooks/use-trip-plan";

// Well-known Rio points inside the OTP graph's Greater-Rio coverage box.
const PLACES = {
  copacabana: { label: "Copacabana", coord: { lat: -22.9711, lon: -43.1822 } },
  centro: { label: "Centro (Carioca)", coord: { lat: -22.9068, lon: -43.1795 } },
  maracana: { label: "Maracanã", coord: { lat: -22.9121, lon: -43.2302 } },
  barra: { label: "Barra da Tijuca", coord: { lat: -22.999, lon: -43.365 } },
  galeao: { label: "Aeroporto (Galeão)", coord: { lat: -22.809, lon: -43.2506 } },
  niteroi: { label: "Niterói (Centro)", coord: { lat: -22.895, lon: -43.123 } },
} satisfies Record<string, { label: string; coord: LatLon }>;

type PlaceKey = keyof typeof PLACES;

const fmtClock = (iso: string): string =>
  new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  }).format(new Date(iso));

const fmtDuration = (seconds: number): string => {
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
};

const modeLabel = (leg: Itinerary["legs"][number]): string => {
  if (leg.mode === "WALK") return "A pé";
  const name = leg.route_short_name ?? leg.route_long_name ?? leg.mode;
  return `${leg.mode === "BUS" ? "Ônibus" : leg.mode} ${name}`;
};

const fieldClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

export const PlannerClient = () => {
  const [originKey, setOriginKey] = useState<PlaceKey>("copacabana");
  const [destKey, setDestKey] = useState<PlaceKey>("centro");
  const [request, setRequest] = useState<PlanTripRequest | null>(null);
  const [selected, setSelected] = useState(0);
  const { data, isFetching, error } = useTripPlan(request);

  const submit = () => {
    setSelected(0);
    setRequest({
      origin: PLACES[originKey].coord,
      destination: PLACES[destKey].coord,
      maxItineraries: 3,
    });
  };

  const itineraries = data ?? [];
  const active = itineraries[selected] ?? null;
  const sameEndpoints = originKey === destKey;

  return (
    <main className="relative h-screen w-screen overflow-hidden">
      <TripPlanMap itinerary={active} />
      <div className="pointer-events-none absolute inset-0 z-10 flex flex-col gap-3 p-4">
        <Surface overlay padding="sm" className="pointer-events-auto max-w-md">
          <Stack gap="sm">
            <Stack direction="row" gap="sm" align="center" justify="between">
              <Heading variant="page">Planejar viagem</Heading>
              <Link href="/" className="text-xs text-muted-foreground hover:text-foreground">
                ← Mapa
              </Link>
            </Stack>
            <Stack gap="xs">
              <Text variant="label" muted>
                Origem
              </Text>
              <select
                aria-label="Origem"
                className={fieldClass}
                value={originKey}
                onChange={(e) => setOriginKey(e.target.value as PlaceKey)}
              >
                {Object.entries(PLACES).map(([k, p]) => (
                  <option key={k} value={k}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Stack>
            <Stack gap="xs">
              <Text variant="label" muted>
                Destino
              </Text>
              <select
                aria-label="Destino"
                className={fieldClass}
                value={destKey}
                onChange={(e) => setDestKey(e.target.value as PlaceKey)}
              >
                {Object.entries(PLACES).map(([k, p]) => (
                  <option key={k} value={k}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Stack>
            <Button onClick={submit} disabled={sameEndpoints || isFetching}>
              {isFetching ? "Planejando..." : "Planejar"}
            </Button>
            {sameEndpoints ? (
              <Text variant="caption" muted>
                Escolha origem e destino diferentes.
              </Text>
            ) : null}
          </Stack>
        </Surface>

        {request !== null ? (
          <Surface
            overlay
            padding="sm"
            className="pointer-events-auto max-w-md flex-1 overflow-y-auto"
          >
            {isFetching ? (
              <Stack gap="sm">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </Stack>
            ) : error ? (
              <Text variant="caption" className="text-destructive">
                Não foi possível planejar a viagem.
              </Text>
            ) : itineraries.length === 0 ? (
              <Text variant="caption" muted>
                Nenhuma rota de transporte público encontrada para esse trajeto.
              </Text>
            ) : (
              <Stack gap="sm">
                <Stack direction="row" gap="xs" align="center">
                  {itineraries.map((it, i) => (
                    <Button
                      key={`${it.start_time}-${i}`}
                      size="sm"
                      variant={i === selected ? "default" : "outline"}
                      onClick={() => setSelected(i)}
                    >
                      {fmtDuration(it.duration_s)}
                    </Button>
                  ))}
                </Stack>
                {active ? <ItineraryDetail itinerary={active} /> : null}
              </Stack>
            )}
          </Surface>
        ) : null}
      </div>
    </main>
  );
};

const connLabel = (c: Itinerary["connections"][number]): string => {
  const route = `${c.from_route ?? "?"} → ${c.to_route ?? "?"}`;
  if (c.kind === "INTERLINE") return `${route} · mesma viagem (sem troca)`;
  return `${route} · espera ${c.wait_minutes} min`;
};

const ItineraryDetail = ({ itinerary }: { itinerary: Itinerary }) => {
  const hasTight = itinerary.connections.some((c) => c.kind === "TIGHT");
  return (
    <Stack gap="sm">
      <Stack direction="row" gap="sm" align="center">
        <Text variant="body">
          {fmtClock(itinerary.start_time)} → {fmtClock(itinerary.end_time)}
        </Text>
        <Badge variant="secondary">
          {itinerary.transfers === 0
            ? "Sem baldeação"
            : `${itinerary.transfers} baldeação${itinerary.transfers > 1 ? "s" : ""}`}
        </Badge>
        {hasTight ? <Badge variant="destructive">Conexão apertada</Badge> : null}
      </Stack>
      <Stack gap="xs">
        {itinerary.legs.map((leg, i) => (
          <Stack
            key={`${leg.mode}-${leg.start_time}-${i}`}
            direction="row"
            gap="sm"
            align="center"
            justify="between"
          >
            <Text variant="caption">{modeLabel(leg)}</Text>
            <Text variant="caption" muted>
              {fmtDuration(leg.duration_s)}
            </Text>
          </Stack>
        ))}
      </Stack>
      {itinerary.connections.length > 0 ? (
        <Stack gap="xs">
          <Text variant="label" muted>
            Baldeações
          </Text>
          {itinerary.connections.map((c, i) => (
            <Text
              key={`${c.from_route}-${c.to_route}-${i}`}
              variant="caption"
              muted={c.kind !== "TIGHT"}
              className={c.kind === "TIGHT" ? "text-destructive" : undefined}
            >
              {connLabel(c)}
              {c.kind === "TIGHT" ? " — apertada" : ""}
            </Text>
          ))}
          <Text variant="caption" muted>
            Conexões estimadas pela folga entre veículos (o Rio não publica baldeações garantidas).
          </Text>
        </Stack>
      ) : null}
    </Stack>
  );
};
