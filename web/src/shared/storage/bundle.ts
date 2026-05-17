"use client";

import { type IDBPDatabase, openDB } from "idb";

import type { OfflineBundle } from "@/shared/api/snapshot";

// Separate IndexedDB database from `favorites` on purpose: the bundle is bulky
// and regenerated, and keeping it apart avoids coupling its lifecycle to the
// favorites store's schema/versioning.
const DB_NAME = "vambora-bundle";
const DB_VERSION = 1;
const STORE = "bundle";
const KEY = "current";

let _db: Promise<IDBPDatabase> | null = null;

const db = (): Promise<IDBPDatabase> => {
  if (_db) return _db;
  _db = openDB(DB_NAME, DB_VERSION, {
    upgrade(database) {
      if (!database.objectStoreNames.contains(STORE)) {
        database.createObjectStore(STORE);
      }
    },
  });
  return _db;
};

export const saveBundle = async (bundle: OfflineBundle): Promise<void> => {
  const conn = await db();
  await conn.put(STORE, bundle, KEY);
};

export const getBundle = async (): Promise<OfflineBundle | null> => {
  const conn = await db();
  return ((await conn.get(STORE, KEY)) as OfflineBundle | undefined) ?? null;
};

export const getBundleMeta = async (): Promise<OfflineBundle["meta"] | null> => {
  return (await getBundle())?.meta ?? null;
};

export const clearBundle = async (): Promise<void> => {
  const conn = await db();
  await conn.delete(STORE, KEY);
};
