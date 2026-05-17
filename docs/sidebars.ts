import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  main: [
    "intro",
    {
      type: "category",
      label: "Architecture",
      items: [
        "architecture/overview",
        "architecture/context-diagram",
        "architecture/container-diagram",
        "architecture/data-flow",
      ],
    },
    {
      type: "category",
      label: "ADRs",
      items: ["adrs/index"],
    },
    {
      type: "category",
      label: "Domain",
      items: ["domain/ubiquitous-language", "domain/tracking"],
    },
    {
      type: "category",
      label: "Design",
      items: ["design/tokens", "design/components"],
    },
    {
      type: "category",
      label: "Data sources",
      items: ["data-sources/sppo"],
    },
    {
      type: "category",
      label: "Development",
      items: ["development/setup", "development/conventions"],
    },
  ],
};

export default sidebars;
