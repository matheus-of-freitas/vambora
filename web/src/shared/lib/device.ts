"use client";

// Anonymous, per-browser device id (plan.md glossary: "Device ID"). Scopes
// alerts before any optional Phase 2 login. localStorage is enough — it
// survives reloads and is fine to lose (a new id just means new alerts).
const KEY = "vambora-device-id";

export const getDeviceId = (): string => {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(KEY, id);
  }
  return id;
};
