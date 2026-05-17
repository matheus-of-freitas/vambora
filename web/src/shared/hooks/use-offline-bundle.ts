"use client";

import { useCallback, useEffect, useState } from "react";

import { type OfflineBundle, fetchBundle, fetchSnapshotLatest } from "@/shared/api/snapshot";
import { getBundleMeta, saveBundle } from "@/shared/storage/bundle";

type Status = "checking" | "absent" | "stored" | "downloading" | "error";

interface OfflineBundleState {
  status: Status;
  meta: OfflineBundle["meta"] | null;
  error: string | null;
  download: () => Promise<void>;
}

export const useOfflineBundle = (): OfflineBundleState => {
  const [status, setStatus] = useState<Status>("checking");
  const [meta, setMeta] = useState<OfflineBundle["meta"] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getBundleMeta()
      .then((m) => {
        if (!active) return;
        setMeta(m);
        setStatus(m ? "stored" : "absent");
      })
      .catch(() => active && setStatus("absent"));
    return () => {
      active = false;
    };
  }, []);

  const download = useCallback(async () => {
    setStatus("downloading");
    setError(null);
    try {
      const latest = await fetchSnapshotLatest();
      if (!latest) {
        setError("Nenhum pacote disponível no servidor.");
        setStatus("error");
        return;
      }
      const bundle = await fetchBundle(latest.url);
      await saveBundle(bundle);
      setMeta(bundle.meta);
      setStatus("stored");
    } catch {
      setError("Falha ao baixar o pacote. Verifique a conexão.");
      setStatus("error");
    }
  }, []);

  return { status, meta, error, download };
};
