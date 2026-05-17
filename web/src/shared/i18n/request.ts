import { getRequestConfig } from "next-intl/server";

import ptBR from "../../../messages/pt-BR.json";

const DEFAULT_LOCALE = "pt-BR";

export default getRequestConfig(async () => ({
  locale: DEFAULT_LOCALE,
  messages: ptBR,
  timeZone: "America/Sao_Paulo",
}));
