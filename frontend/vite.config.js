import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  root: "public",
  build: {
    outDir: "../dist",
  },
  css: {
    postcss: path.resolve(__dirname, "postcss.config.js"),
  },
  server: {
    open: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000/api", // TODO: Production/Dev URL
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
