import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 6610,
    proxy: {
      "/api": {
        target: "http://backend:6600",
        changeOrigin: true,
        ws: true,
      },
      "/events": {
        target: "http://code_manager:5001",
        changeOrigin: true,
      },
      "/run_code_streaming": {
        target: "http://code_manager:5001",
        changeOrigin: true,
      },
    },
  },
});
