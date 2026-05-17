"use client";

import { useTranslations } from "next-intl";

import { Surface } from "@/shared/components/layout/surface";
import { Text } from "@/shared/components/layout/text";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useLiveVehicles } from "@/shared/hooks/use-live-vehicles";

export const StatusBar = () => {
  const t = useTranslations("map");
  const { data, isLoading, error } = useLiveVehicles();
  const count = data?.length ?? 0;

  if (error) {
    return (
      <Surface overlay padding="sm" className="border border-destructive/40">
        <Text variant="caption" className="text-destructive">
          {t("error")}
        </Text>
      </Surface>
    );
  }
  if (isLoading) {
    return (
      <Surface overlay padding="sm">
        <Skeleton className="h-4 w-24" />
      </Surface>
    );
  }
  return (
    <Surface overlay padding="sm">
      <Text variant="caption">{t("vehicles", { count })}</Text>
    </Surface>
  );
};
