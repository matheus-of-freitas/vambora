"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { type ReactNode, useState } from "react";

import type { AbstractIntlMessages } from "next-intl";

interface Props {
  children: ReactNode;
  locale: string;
  messages: AbstractIntlMessages;
}

export const Providers = ({ children, locale, messages }: Props) => {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { refetchOnWindowFocus: false, retry: 1 },
        },
      }),
  );
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </NextIntlClientProvider>
  );
};
