import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { ServiceWorkerRegistrar } from "@/shared/components/system/service-worker-registrar";
import { BRAND } from "@/shared/lib/branding";
import { Providers } from "./providers";
import "./globals.css";

import ptBR from "../../messages/pt-BR.json";

export const metadata: Metadata = {
  title: "Vambora",
  description: "Seu transporte público no Rio em tempo real.",
  manifest: "/manifest.webmanifest",
  applicationName: "Vambora",
  appleWebApp: {
    title: "Vambora",
    capable: true,
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: BRAND.themeColor,
  width: "device-width",
  initialScale: 1,
};

const RootLayout = ({ children }: { children: ReactNode }) => (
  <html lang="pt-BR" className="dark">
    <body>
      <Providers locale="pt-BR" messages={ptBR}>
        {children}
      </Providers>
      <ServiceWorkerRegistrar />
    </body>
  </html>
);

export default RootLayout;
