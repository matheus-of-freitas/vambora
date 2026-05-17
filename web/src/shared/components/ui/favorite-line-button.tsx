"use client";

import { Star } from "lucide-react";

import { useFavorites } from "@/shared/hooks/use-favorites";
import { cn } from "@/shared/lib/utils";

interface Props {
  shortName: string;
}

export const FavoriteLineButton = ({ shortName }: Props) => {
  const { isFavoriteLine, toggleLine, hydrated } = useFavorites();
  const active = hydrated && isFavoriteLine(shortName);

  return (
    <button
      type="button"
      onClick={() => void toggleLine(shortName)}
      aria-label={active ? "Remover dos favoritos" : "Adicionar aos favoritos"}
      aria-pressed={active}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors",
        "hover:bg-accent/40 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        active ? "text-primary" : "text-muted-foreground",
      )}
    >
      <Star aria-hidden className={cn("h-4 w-4", active && "fill-current")} />
    </button>
  );
};
