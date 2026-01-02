// ✅ src/config.js
// Centralized configuration for all frontend API + WebSocket connections
// Ensures consistent behavior across local dev, staging, and production environments

// -----------------------------
// 🌍 ENVIRONMENT + MODE DETECTION
// -----------------------------
const isDev = import.meta.env.DEV;
const hostname = window?.location?.hostname || "production";

// -----------------------------
// 🔗 API BASE (Backend URL)
// -----------------------------
const PROD_API = "https://api.simbawaujamaa.com";
const DEV_API = "http://localhost:3000";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (hostname === "localhost" ? DEV_API : PROD_API);

// Legacy alias (for backward compatibility)
export const API_BASE = API_BASE_URL;

// -----------------------------
// 🦁 FRONTEND BASE (App URL)
// -----------------------------
const PROD_APP = "https://simbawaujamaa.com";
const DEV_APP = "http://localhost:5173";

export const APP_BASE_URL =
  import.meta.env.VITE_APP_BASE_URL ||
  (hostname === "localhost" ? DEV_APP : PROD_APP);

// -----------------------------
// 🔌 WEBSOCKET BASE (Realtime)
// -----------------------------
const PROD_WS = "wss://api.simbawaujamaa.com";
const DEV_WS = "ws://localhost:3000";

export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL ||
  (hostname === "localhost" ? DEV_WS : PROD_WS);

// -----------------------------
// 🧩 UTILITY FLAGS
// -----------------------------
export const ENV = {
  mode: isDev ? "development" : "production",
  isDev,
  isProd: !isDev,
};

// -----------------------------
// ✅ LOG CONFIG SUMMARY (Dev only)
// -----------------------------
if (isDev) {
  console.groupCollapsed("✅ Mufasa Config Loaded");
  console.table({
    API_BASE_URL,
    APP_BASE_URL,
    WS_BASE_URL,
    Mode: ENV.mode,
  });
  console.groupEnd();
}
