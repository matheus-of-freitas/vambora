import type { Schemas } from "./openapi";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

// Generated from the backend OpenAPI schema (see openapi.ts / `pnpm gen:api`).
export type AlertRule = Schemas["AlertRuleDTO"];
export type CreateAlertRuleInput = Schemas["CreateAlertRuleRequest"];

export const listAlertRules = async (
  deviceId: string,
  options: { signal?: AbortSignal } = {},
): Promise<AlertRule[]> => {
  const url = new URL(`${baseUrl()}/alerts/rules`);
  url.searchParams.set("device_id", deviceId);
  const response = await fetch(url, { signal: options.signal });
  if (!response.ok) throw new Error(`alerts/rules: HTTP ${response.status}`);
  return (await response.json()) as AlertRule[];
};

export const createAlertRule = async (input: CreateAlertRuleInput): Promise<AlertRule> => {
  const response = await fetch(`${baseUrl()}/alerts/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (response.status === 400) {
    const detail = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(detail.detail ?? "Pedido inválido");
  }
  if (!response.ok) throw new Error(`create alert: HTTP ${response.status}`);
  return (await response.json()) as AlertRule;
};

export const deleteAlertRule = async (ruleId: string): Promise<void> => {
  const response = await fetch(`${baseUrl()}/alerts/rules/${encodeURIComponent(ruleId)}`, {
    method: "DELETE",
  });
  if (response.status !== 204 && response.status !== 404) {
    throw new Error(`delete alert: HTTP ${response.status}`);
  }
};
