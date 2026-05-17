"use client";

import {
  type AlertRule,
  type CreateAlertRuleInput,
  createAlertRule,
  deleteAlertRule,
  listAlertRules,
} from "@/shared/api/alerts";
import { getDeviceId } from "@/shared/lib/device";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

interface AlertsState {
  deviceId: string;
  rules: AlertRule[];
  isLoading: boolean;
  create: (input: Omit<CreateAlertRuleInput, "device_id">) => Promise<void>;
  remove: (ruleId: string) => Promise<void>;
  createError: string | null;
}

export const useAlerts = (): AlertsState => {
  const qc = useQueryClient();
  const [deviceId, setDeviceId] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    setDeviceId(getDeviceId());
  }, []);

  const key = ["alerts", deviceId];
  const query = useQuery<AlertRule[]>({
    queryKey: key,
    queryFn: ({ signal }) => listAlertRules(deviceId, { signal }),
    enabled: deviceId !== "",
    refetchInterval: 30_000,
  });

  const createMut = useMutation({
    mutationFn: (input: Omit<CreateAlertRuleInput, "device_id">) =>
      createAlertRule({ ...input, device_id: deviceId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  const deleteMut = useMutation({
    mutationFn: (ruleId: string) => deleteAlertRule(ruleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  const create = async (input: Omit<CreateAlertRuleInput, "device_id">): Promise<void> => {
    setCreateError(null);
    try {
      await createMut.mutateAsync(input);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Falha ao criar alerta");
    }
  };

  return {
    deviceId,
    rules: query.data ?? [],
    isLoading: query.isLoading,
    create,
    remove: async (ruleId: string) => {
      await deleteMut.mutateAsync(ruleId);
    },
    createError,
  };
};
