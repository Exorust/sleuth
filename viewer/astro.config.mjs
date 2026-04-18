import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  site: "https://rlm.sh",
  integrations: [tailwind({ applyBaseStyles: false })],
  output: "static",
  build: { assets: "_assets" },
});
