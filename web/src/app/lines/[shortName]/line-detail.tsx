"use client";

import Link from "next/link";

import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { LineVehiclesMap } from "@/shared/components/map/line-vehicles-map";
import { Badge } from "@/shared/components/ui/badge";
import { FavoriteLineButton } from "@/shared/components/ui/favorite-line-button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useLineRealtime } from "@/shared/hooks/use-line-realtime";
import { useLineShape } from "@/shared/hooks/use-line-shape";

interface Props {
  shortName: string;
}

export const LineDetail = ({ shortName }: Props) => {
  const { data, isLoading, error } = useLineRealtime(shortName);
  const { data: shape } = useLineShape(shortName);
  const routeColor = data?.routes[0]?.color ?? null;

  return (
    <main className="relative h-screen w-screen overflow-hidden">
      <LineVehiclesMap
        vehicles={data?.vehicles ?? []}
        shape={shape ?? null}
        routeColorHex={routeColor}
      />
      <header className="pointer-events-none absolute left-0 right-0 top-0 z-10 flex items-start justify-between gap-2 p-4">
        <Surface overlay padding="sm" className="pointer-events-auto max-w-md">
          <Stack gap="xs">
            <Stack direction="row" gap="sm" align="center">
              <Link href="/" className="text-xs text-muted-foreground hover:text-foreground">
                ← Mapa
              </Link>
              {data?.routes[0]?.color ? <ColorChip hex={data.routes[0].color} /> : null}
              <Heading variant="page">{shortName}</Heading>
              <FavoriteLineButton shortName={shortName} />
            </Stack>
            {error ? (
              <Text variant="caption" className="text-destructive">
                Não foi possível carregar a linha.
              </Text>
            ) : isLoading ? (
              <Skeleton className="h-3 w-40" />
            ) : data == null ? (
              <Text variant="caption" muted>
                Linha não encontrada no catálogo.
              </Text>
            ) : (
              <Stack gap="xs">
                {data.routes.map((r) => (
                  <Text key={r.route_id} variant="caption" muted>
                    {r.long_name}
                  </Text>
                ))}
              </Stack>
            )}
          </Stack>
        </Surface>
        <Surface overlay padding="sm" className="pointer-events-auto">
          {isLoading ? (
            <Skeleton className="h-4 w-28" />
          ) : data == null ? null : data.vehicles.length > 0 ? (
            <Stack direction="row" gap="sm" align="center">
              <Badge>Ao vivo</Badge>
              <Text variant="caption">
                {data.vehicles.length} {data.vehicles.length === 1 ? "ônibus" : "ônibus"}
              </Text>
            </Stack>
          ) : (
            <Badge variant="secondary">Apenas programado</Badge>
          )}
        </Surface>
      </header>
    </main>
  );
};

const ColorChip = ({ hex }: { hex: string }) => (
  <span
    aria-hidden
    className="inline-block h-3 w-3 rounded-sm"
    style={{ backgroundColor: `#${hex}` }}
  />
);
