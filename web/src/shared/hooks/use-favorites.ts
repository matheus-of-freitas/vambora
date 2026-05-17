"use client";

import { useEffect } from "react";
import { create } from "zustand";

import {
  type Favorite,
  addLineFavorite,
  addStopFavorite,
  getAllFavorites,
  removeLineFavorite,
  removeStopFavorite,
} from "@/shared/storage/favorites";

interface FavoritesState {
  favorites: Favorite[];
  hydrated: boolean;
  hydrate: () => Promise<void>;
  toggleLine: (shortName: string) => Promise<void>;
  toggleStop: (stopId: string, name: string) => Promise<void>;
}

const useStore = create<FavoritesState>((set, get) => ({
  favorites: [],
  hydrated: false,

  hydrate: async () => {
    if (get().hydrated) return;
    const favorites = await getAllFavorites();
    set({ favorites, hydrated: true });
  },

  toggleLine: async (shortName: string) => {
    const isFav = get().favorites.some((f) => f.kind === "line" && f.short_name === shortName);
    if (isFav) {
      await removeLineFavorite(shortName);
    } else {
      await addLineFavorite(shortName);
    }
    set({ favorites: await getAllFavorites() });
  },

  toggleStop: async (stopId: string, name: string) => {
    const isFav = get().favorites.some((f) => f.kind === "stop" && f.stop_id === stopId);
    if (isFav) {
      await removeStopFavorite(stopId);
    } else {
      await addStopFavorite(stopId, name);
    }
    set({ favorites: await getAllFavorites() });
  },
}));

export const useFavorites = (): {
  favorites: Favorite[];
  hydrated: boolean;
  isFavoriteLine: (shortName: string) => boolean;
  isFavoriteStop: (stopId: string) => boolean;
  toggleLine: (shortName: string) => Promise<void>;
  toggleStop: (stopId: string, name: string) => Promise<void>;
} => {
  const state = useStore();

  useEffect(() => {
    if (!state.hydrated) {
      void state.hydrate();
    }
  }, [state]);

  return {
    favorites: state.favorites,
    hydrated: state.hydrated,
    isFavoriteLine: (shortName) =>
      state.favorites.some((f) => f.kind === "line" && f.short_name === shortName),
    isFavoriteStop: (stopId) =>
      state.favorites.some((f) => f.kind === "stop" && f.stop_id === stopId),
    toggleLine: state.toggleLine,
    toggleStop: state.toggleStop,
  };
};
