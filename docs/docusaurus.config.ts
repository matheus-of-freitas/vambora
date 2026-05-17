import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "Vambora",
  tagline: "Real-time public transit for Rio de Janeiro",
  favicon: "img/favicon.ico",
  url: "https://docs.vambora.app",
  baseUrl: "/",
  organizationName: "vambora",
  projectName: "vambora-docs",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  i18n: { defaultLocale: "en", locales: ["en"] },
  future: { v4: true, faster: true },
  markdown: { mermaid: true },
  themes: ["@docusaurus/theme-mermaid"],
  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          routeBasePath: "/",
        },
        blog: false,
        theme: { customCss: "./src/css/custom.css" },
      } satisfies Preset.Options,
    ],
  ],
  themeConfig: {
    colorMode: { defaultMode: "dark", respectPrefersColorScheme: true },
    navbar: {
      title: "Vambora",
      items: [
        { type: "docSidebar", sidebarId: "main", position: "left", label: "Docs" },
        { href: "https://github.com/vambora", label: "GitHub", position: "right" },
      ],
    },
    footer: {
      style: "dark",
      copyright: `© ${new Date().getFullYear()} Vambora. MIT licensed.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ["bash", "python", "kotlin", "sql"],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
