"use client";

import Link from "next/link";
import { useState } from "react";

import type { AlertRule } from "@/shared/api/alerts";
import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { SingleStopMap } from "@/shared/components/map/single-stop-map";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { FavoriteStopButton } from "@/shared/components/ui/favorite-stop-button";
import { Input } from "@/shared/components/ui/input";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useAlerts } from "@/shared/hooks/use-alerts";
import { useOfflineStopLines } from "@/shared/hooks/use-offline-stop-lines";
import { useStop } from "@/shared/hooks/use-stop";
import { useStopArrivals } from "@/shared/hooks/use-stop-arrivals";
import { useStopPredictions } from "@/shared/hooks/use-stop-predictions";
import { useNowSecondsBRT } from "@/shared/lib/clock";

interface Props {
  stopId: string;
}

export const StopDetail = ({ stopId }: Props) => {
  const { data, isLoading, error } = useStop(stopId);
  const { data: arrivals, isLoading: arrivalsLoading } = useStopArrivals(stopId, 10);
  const { data: predictions, isLoading: predictionsLoading } = useStopPredictions(stopId, 8);
  const offlineLines = useOfflineStopLines(stopId);
  const nowSec = useNowSecondsBRT();
  const hasLive = (predictions?.length ?? 0) > 0;
  const lineOptions = Array.from(
    new Set([
      ...(predictions ?? []).map((p) => p.line_short_name),
      ...(arrivals ?? []).map((a) => a.route_short_name),
    ]),
  ).sort();

  return (
    <main className="relative h-screen w-screen overflow-hidden">
      {data ? (
        <SingleStopMap longitude={data.longitude} latitude={data.latitude} />
      ) : (
        <div className="absolute inset-0 bg-background" />
      )}
      <header className="pointer-events-none absolute left-0 right-0 top-0 z-10 flex items-start justify-between gap-2 p-4">
        <Surface
          overlay
          padding="sm"
          className="pointer-events-auto max-w-md max-h-screen overflow-y-auto"
        >
          <Stack gap="xs">
            <Stack direction="row" gap="sm" align="center">
              <Link href="/" className="text-xs text-muted-foreground hover:text-foreground">
                ← Mapa
              </Link>
              <Heading variant="page">{data?.name ?? "Parada"}</Heading>
              {data ? <FavoriteStopButton stopId={data.stop_id} name={data.name} /> : null}
            </Stack>
            {error ? (
              <Text variant="caption" className="text-destructive">
                Não foi possível carregar a parada.
              </Text>
            ) : isLoading ? (
              <Skeleton className="h-3 w-40" />
            ) : data == null ? (
              <Text variant="caption" muted>
                Parada não encontrada no catálogo.
              </Text>
            ) : (
              <Stack gap="xs">
                <Text variant="caption" muted>
                  ID: {data.stop_id}
                </Text>
                {data.code ? (
                  <Text variant="caption" muted>
                    Código: {data.code}
                  </Text>
                ) : null}
                {data.parent_station ? (
                  <Text variant="caption" muted>
                    Estação pai: {data.parent_station}
                  </Text>
                ) : null}
                {data.wheelchair_boarding === 1 ? (
                  <Text variant="caption">Acessível para cadeirantes</Text>
                ) : data.wheelchair_boarding === 2 ? (
                  <Text variant="caption" muted>
                    Sem acesso para cadeirantes
                  </Text>
                ) : null}

                <Stack gap="xs" className="pt-2">
                  <Stack direction="row" gap="sm" align="center">
                    <Heading level={2} variant="section">
                      Chegando agora
                    </Heading>
                    {hasLive ? (
                      <Badge>Ao vivo</Badge>
                    ) : (
                      <Badge variant="secondary">Sem dados ao vivo</Badge>
                    )}
                  </Stack>
                  {predictionsLoading ? (
                    <Skeleton className="h-12 w-full" />
                  ) : !hasLive ? (
                    <Text variant="caption" muted>
                      Nenhum ônibus se aproximando no momento. Veja os horários programados abaixo.
                    </Text>
                  ) : (
                    <Stack gap="xs">
                      {predictions?.map((p) => (
                        <PredictionRow key={`${p.line_short_name}-${p.vehicle_id}`} p={p} />
                      ))}
                    </Stack>
                  )}
                </Stack>

                <Stack gap="xs" className="pt-2">
                  <Stack direction="row" gap="sm" align="center">
                    <Heading level={2} variant="section">
                      Próximas saídas
                    </Heading>
                    <Badge variant="secondary">Programado</Badge>
                  </Stack>
                  {arrivalsLoading ? (
                    <Skeleton className="h-16 w-full" />
                  ) : !arrivals || arrivals.length === 0 ? (
                    offlineLines.length > 0 ? (
                      <Stack gap="xs">
                        <Text variant="caption" muted>
                          Sem horários ao vivo. Linhas que passam aqui (frequência típica):
                        </Text>
                        {offlineLines.map((l) => (
                          <Link
                            key={l.short_name}
                            href={`/lines/${encodeURIComponent(l.short_name)}`}
                            className="block rounded-sm hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          >
                            <Stack direction="row" gap="sm" align="center">
                              <span className="text-xs font-semibold">{l.short_name}</span>
                              <Text variant="caption" muted>
                                {l.headway_minutes
                                  ? `a cada ~${l.headway_minutes} min`
                                  : "frequência não informada"}
                              </Text>
                            </Stack>
                          </Link>
                        ))}
                      </Stack>
                    ) : (
                      <Text variant="caption" muted>
                        Sem horários previstos.
                      </Text>
                    )
                  ) : (
                    <Stack gap="xs">
                      {arrivals.map((a) => (
                        <ArrivalRow
                          key={`${a.trip_id}-${a.arrival_seconds}`}
                          arrival={a}
                          nowSec={nowSec}
                        />
                      ))}
                    </Stack>
                  )}
                </Stack>

                <AlertsSection stopId={stopId} lines={lineOptions} />
              </Stack>
            )}
          </Stack>
        </Surface>
      </header>
    </main>
  );
};

const ArrivalRow = ({
  arrival,
  nowSec,
}: {
  arrival: import("@/shared/api/stop-arrivals").ScheduledArrival;
  nowSec: number;
}) => {
  const relative = formatRelative(arrival.arrival_seconds - nowSec);
  return (
    <Link
      href={`/lines/${encodeURIComponent(arrival.route_short_name)}`}
      className="block rounded-sm hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
    >
      <Stack direction="row" gap="sm" align="center">
        <span className="font-mono text-xs tabular-nums w-12">{arrival.arrival_time}</span>
        {relative ? (
          <span className="text-xs text-muted-foreground tabular-nums w-16">{relative}</span>
        ) : (
          <span className="w-16" />
        )}
        {arrival.route_color ? (
          <span
            aria-hidden
            className="inline-block h-2 w-2 rounded-sm"
            style={{ backgroundColor: `#${arrival.route_color}` }}
          />
        ) : null}
        <span className="text-xs font-semibold">{arrival.route_short_name}</span>
        {arrival.headsign ? (
          <Text variant="caption" muted className="truncate">
            {arrival.headsign}
          </Text>
        ) : null}
      </Stack>
    </Link>
  );
};

const PredictionRow = ({
  p,
}: {
  p: import("@/shared/api/stop-predictions").ArrivalPrediction;
}) => {
  const dist =
    p.distance_m >= 1000
      ? `${(p.distance_m / 1000).toFixed(1)} km`
      : `${Math.round(p.distance_m)} m`;
  return (
    <Link
      href={`/lines/${encodeURIComponent(p.line_short_name)}`}
      className="block rounded-sm hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
    >
      <Stack direction="row" gap="sm" align="center">
        <span className="font-mono text-xs font-semibold tabular-nums w-12">
          {p.eta_minutes} min
        </span>
        {p.route_color ? (
          <span
            aria-hidden
            className="inline-block h-2 w-2 rounded-sm"
            style={{ backgroundColor: `#${p.route_color}` }}
          />
        ) : null}
        <span className="text-xs font-semibold">{p.line_short_name}</span>
        <Text variant="caption" muted className="truncate">
          {dist}
        </Text>
      </Stack>
    </Link>
  );
};

const formatRelative = (deltaSec: number): string | null => {
  if (deltaSec < -60) return null;
  if (deltaSec < 60) return "agora";
  if (deltaSec < 3600) return `em ${Math.round(deltaSec / 60)} min`;
  return null;
};

const fieldClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

const fmtTriggered = (iso: string): string =>
  new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  }).format(new Date(iso));

const AlertsSection = ({ stopId, lines }: { stopId: string; lines: string[] }) => {
  const { rules, isLoading, create, remove, createError } = useAlerts();
  const [line, setLine] = useState("");
  const [threshold, setThreshold] = useState(5);
  const selectedLine = line || lines[0] || "";
  const stopRules = rules.filter((r) => r.stop_id === stopId);

  return (
    <Stack gap="xs" className="pt-2">
      <Stack direction="row" gap="sm" align="center">
        <Heading level={2} variant="section">
          Alertas
        </Heading>
        <Badge variant="secondary">Beta</Badge>
      </Stack>

      {lines.length === 0 ? (
        <Text variant="caption" muted>
          Nenhuma linha conhecida nesta parada para criar um alerta.
        </Text>
      ) : (
        <Stack gap="xs">
          <select
            aria-label="Linha do alerta"
            className={fieldClass}
            value={selectedLine}
            onChange={(e) => setLine(e.target.value)}
          >
            {lines.map((l) => (
              <option key={l} value={l}>
                Linha {l}
              </option>
            ))}
          </select>
          <Stack direction="row" gap="sm" align="center">
            <Input
              type="number"
              aria-label="Minutos de antecedência"
              min={1}
              max={60}
              value={threshold}
              onChange={(e) => setThreshold(Math.max(1, Math.min(60, Number(e.target.value) || 1)))}
              className="h-9 w-20"
            />
            <Text variant="caption" muted>
              min de antecedência
            </Text>
          </Stack>
          <Button
            onClick={() =>
              create({
                line_short_name: selectedLine,
                stop_id: stopId,
                threshold_minutes: threshold,
              })
            }
            disabled={!selectedLine}
          >
            Criar alerta
          </Button>
          {createError ? (
            <Text variant="caption" className="text-destructive">
              {createError}
            </Text>
          ) : null}
        </Stack>
      )}

      {isLoading ? (
        <Skeleton className="h-8 w-full" />
      ) : stopRules.length > 0 ? (
        <Stack gap="xs">
          {stopRules.map((r) => (
            <AlertRuleRow key={r.id} rule={r} onRemove={() => remove(r.id)} />
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
};

const AlertRuleRow = ({
  rule,
  onRemove,
}: {
  rule: AlertRule;
  onRemove: () => void;
}) => (
  <Stack direction="row" gap="sm" align="center" justify="between">
    <Stack direction="row" gap="sm" align="center">
      <span className="text-xs font-semibold">{rule.line_short_name}</span>
      <Text variant="caption" muted>
        {rule.threshold_minutes} min
      </Text>
      {rule.last_triggered_at ? (
        <Badge>Avisado {fmtTriggered(rule.last_triggered_at)}</Badge>
      ) : (
        <Badge variant="secondary">Aguardando</Badge>
      )}
    </Stack>
    <button
      type="button"
      onClick={onRemove}
      aria-label={`Remover alerta da linha ${rule.line_short_name}`}
      className="text-xs text-muted-foreground hover:text-destructive"
    >
      Remover
    </button>
  </Stack>
);
