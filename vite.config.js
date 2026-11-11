import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 本機開發：前端 5173，/api 轉給 Flask（5000）
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
});
