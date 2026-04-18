import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  site: "https://exorust.github.io",
  base: process.env.VIEWER_BASE ?? "/",
  integrations: [tailwind({ applyBaseStyles: false })],
  output: "static",
  build: { assets: "_assets" },
});
