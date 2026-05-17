"use client";

import { useEffect } from "react";

/**
 * Mounts once and registers ``/sw.js``.
 *
 * **By default the SW is only registered in production builds.** Dev Next.js
 * serves content-hashed asset URLs that drift across HMR rebuilds; a SW that
 * caches the HTML shell then references stale chunk hashes can leave pages
 * un-hydrated. To exercise the SW against the dev server (e.g. the PWA e2e
 * suite) set ``NEXT_PUBLIC_ENABLE_SW=1``.
 */
export const ServiceWorkerRegistrar = () => {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;

    const isProduction = process.env.NODE_ENV === "production";
    const forceEnable = process.env.NEXT_PUBLIC_ENABLE_SW === "1";
    if (!isProduction && !forceEnable) return;

    const register = async (): Promise<void> => {
      try {
        await navigator.serviceWorker.register("/sw.js", { scope: "/" });
      } catch (err) {
        console.warn("service worker registration failed", err);
      }
    };
    void register();
  }, []);

  return null;
};
