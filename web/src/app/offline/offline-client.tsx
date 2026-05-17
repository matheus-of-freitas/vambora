"use client";

import Link from "next/link";

import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useOfflineBundle } from "@/shared/hooks/use-offline-bundle";

const fmtDate = (iso: string): string =>
  new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  }).format(new Date(iso));

export const OfflineClient = () => {
  const { status, meta, error, download } = useOfflineBundle();

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Surface padding="lg" className="max-w-md">
        <Stack gap="lg">
          <Stack gap="md">
            <Heading variant="display">Uso offline</Heading>
            <Text>
              Baixe o catálogo (linhas, paradas e traçados) para usar o Vambora sem conexão. As
              posições dos ônibus em tempo real precisam de rede.
            </Text>
          </Stack>

          <Stack gap="sm">
            <Stack direction="row" gap="sm" align="center">
              <Heading level={2} variant="section">
                Pacote de dados
              </Heading>
              {status === "stored" ? (
                <Badge>Salvo no dispositivo</Badge>
              ) : status === "absent" ? (
                <Badge variant="secondary">Não baixado</Badge>
              ) : null}
            </Stack>

            {status === "checking" ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <Stack gap="sm">
                {meta ? (
                  <Stack gap="xs">
                    <Text variant="caption" muted>
                      Versão {meta.version}
                    </Text>
                    <Text variant="caption" muted>
                      Gerado em {fmtDate(meta.generated_at)}
                    </Text>
                    <Text variant="caption" muted>
                      {meta.route_count} linhas · {meta.stop_count} paradas
                    </Text>
                  </Stack>
                ) : null}
                {error ? (
                  <Text variant="caption" className="text-destructive">
                    {error}
                  </Text>
                ) : null}
                <Button onClick={download} disabled={status === "downloading"}>
                  {status === "downloading"
                    ? "Baixando..."
                    : meta
                      ? "Atualizar pacote"
                      : "Baixar dados para uso offline"}
                </Button>
              </Stack>
            )}
          </Stack>

          <Link href="/" className="text-xs text-muted-foreground hover:text-foreground">
            ← Voltar ao mapa
          </Link>
        </Stack>
      </Surface>
    </main>
  );
};
