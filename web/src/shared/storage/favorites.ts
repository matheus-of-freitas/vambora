"use client";

import { type IDBPDatabase, openDB } from "idb";

const DB_NAME = "vambora";
const DB_VERSION = 1;
const STORE = "favorites";

export type FavoriteKind = "line" | "stop";

export interface FavoriteLine {
  kind: "line";
  short_name: string;
  added_at: string;
}

export interface FavoriteStop {
  kind: "stop";
  stop_id: string;
  name: string;
  added_at: string;
}

export type Favorite = FavoriteLine | FavoriteStop;

const keyFor = (f: Favorite): string =>
  f.kind === "line" ? `line:${f.short_name}` : `stop:${f.stop_id}`;

const lineKey = (shortName: string): string => `line:${shortName}`;
const stopKey = (stopId: string): string => `stop:${stopId}`;

let _db: Promise<IDBPDatabase> | null = null;

const db = (): Promise<IDBPDatabase> => {
  if (_db) return _db;
  _db = openDB(DB_NAME, DB_VERSION, {
    upgrade(database) {
      if (!database.objectStoreNames.contains(STORE)) {
        database.createObjectStore(STORE, { keyPath: "key" });
      }
    },
  });
  return _db;
};

interface StoredFavorite {
  key: string;
  value: Favorite;
}

export const getAllFavorites = async (): Promise<Favorite[]> => {
  const conn = await db();
  const all = (await conn.getAll(STORE)) as StoredFavorite[];
  return all.map((row) => row.value).sort((a, b) => b.added_at.localeCompare(a.added_at));
};

export const addLineFavorite = async (shortName: string): Promise<void> => {
  const conn = await db();
  const value: FavoriteLine = {
    kind: "line",
    short_name: shortName,
    added_at: new Date().toISOString(),
  };
  await conn.put(STORE, { key: keyFor(value), value });
};

export const removeLineFavorite = async (shortName: string): Promise<void> => {
  const conn = await db();
  await conn.delete(STORE, lineKey(shortName));
};

export const addStopFavorite = async (stopId: string, name: string): Promise<void> => {
  const conn = await db();
  const value: FavoriteStop = {
    kind: "stop",
    stop_id: stopId,
    name,
    added_at: new Date().toISOString(),
  };
  await conn.put(STORE, { key: keyFor(value), value });
};

export const removeStopFavorite = async (stopId: string): Promise<void> => {
  const conn = await db();
  await conn.delete(STORE, stopKey(stopId));
};
