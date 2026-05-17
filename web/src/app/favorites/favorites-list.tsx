"use client";

import Link from "next/link";

import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Text } from "@/shared/components/layout/text";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useFavorites } from "@/shared/hooks/use-favorites";

export const FavoritesList = () => {
  const { favorites, hydrated } = useFavorites();
  const lines = favorites.filter(
    (f): f is Extract<(typeof favorites)[number], { kind: "line" }> => f.kind === "line",
  );
  const stops = favorites.filter(
    (f): f is Extract<(typeof favorites)[number], { kind: "stop" }> => f.kind === "stop",
  );

  return (
    <main className="container mx-auto py-10">
      <Stack gap="lg">
        <Stack direction="row" gap="md" align="center" justify="between">
          <Stack gap="xs">
            <Heading variant="display">Favoritos</Heading>
            <Text muted>Linhas e paradas salvas neste dispositivo.</Text>
          </Stack>
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Mapa
          </Link>
        </Stack>

        {!hydrated ? (
          <Stack gap="sm">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </Stack>
        ) : favorites.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Nenhum favorito ainda</CardTitle>
              <CardDescription>Toque na estrela em uma linha para salvá-la aqui.</CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <Stack gap="md">
            {lines.length > 0 ? (
              <Stack gap="sm">
                <Heading level={2} variant="section">
                  Linhas
                </Heading>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {lines.map((f) => (
                    <Link
                      key={`line-${f.short_name}`}
                      href={`/lines/${encodeURIComponent(f.short_name)}`}
                      className="block focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring rounded-md"
                      data-testid={`fav-line-${f.short_name}`}
                    >
                      <Card>
                        <CardHeader>
                          <CardTitle>{f.short_name}</CardTitle>
                          <CardDescription>Salvo em {formatDate(f.added_at)}</CardDescription>
                        </CardHeader>
                      </Card>
                    </Link>
                  ))}
                </div>
              </Stack>
            ) : null}
            {stops.length > 0 ? (
              <Stack gap="sm">
                <Heading level={2} variant="section">
                  Paradas
                </Heading>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {stops.map((f) => (
                    <Card key={`stop-${f.stop_id}`}>
                      <CardHeader>
                        <CardTitle>{f.name}</CardTitle>
                        <CardDescription>
                          {f.stop_id} · Salvo em {formatDate(f.added_at)}
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              </Stack>
            ) : null}
          </Stack>
        )}
      </Stack>
    </main>
  );
};

const formatDate = (iso: string): string => {
  try {
    return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(iso));
  } catch {
    return iso;
  }
};
