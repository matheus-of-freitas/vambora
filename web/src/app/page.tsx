import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { Heading } from "@/shared/components/layout/heading";
import { Stack } from "@/shared/components/layout/stack";
import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { LiveVehiclesMap } from "@/shared/components/map/live-vehicles-map";
import { LineSearch } from "@/shared/components/ui/line-search";
import { StatusBar } from "@/shared/components/ui/status-bar";

const Page = async () => {
  const t = await getTranslations("app");
  return (
    <main className="relative h-screen w-screen overflow-hidden">
      <LiveVehiclesMap />
      <header className="pointer-events-none absolute left-0 right-0 top-0 z-10 flex items-start justify-between p-4">
        <Surface overlay padding="sm" className="pointer-events-auto">
          <Stack gap="sm">
            <Stack direction="row" gap="md" align="center" justify="between">
              <Stack gap="xs">
                <Heading variant="page">{t("title")}</Heading>
                <Text variant="caption" muted>
                  {t("tagline")}
                </Text>
              </Stack>
              <Stack direction="row" gap="sm" align="center">
                <Link
                  href="/planner"
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Planejar
                </Link>
                <Link
                  href="/favorites"
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Favoritos
                </Link>
                <Link
                  href="/offline"
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Offline
                </Link>
              </Stack>
            </Stack>
            <LineSearch />
          </Stack>
        </Surface>
        <div className="pointer-events-auto">
          <StatusBar />
        </div>
      </header>
    </main>
  );
};

export default Page;
