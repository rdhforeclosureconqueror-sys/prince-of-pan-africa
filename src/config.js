// ✅ src/config.js
// Centralized configuration for all frontend API + WebSocket connections
// Ensures consistent behavior across local dev, staging, and production environments

// -----------------------------
// 🌍 ENVIRONMENT + MODE DETECTION
// -----------------------------
const isDev = import.meta.env.DEV;
const hostname = window?.location?.hostname || "production";

// -----------------------------
// 🔗 PRIMARY BACKEND (Simba Waa Ujamaa API)
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
// 🧠 SECONDARY SERVICES (AI + Voice + Knowledge)
// -----------------------------

// Mufasa Knowledge Bank
export const MUFASA_API_URL =
  import.meta.env.VITE_MUFASA_API ||
  "https://mufasa-knowledge-bank.onrender.com";

// OpenVoice / Voice API
export const OPENVOICE_API_URL =
  import.meta.env.VITE_OPENVOICE_API ||
  "https://aivoice-wmrv.onrender.com";

// Optional: Future AI/ML Models (TensorFlow, etc.)
export const AI_MODEL_API_URL =
  import.meta.env.VITE_AI_MODEL_API ||
  `${API_BASE_URL}/ai`;

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
  console.groupCollapsed("✅ Simba Waa Ujamaa Config Loaded");
  console.table({
    "Primary API": API_BASE_URL,
    "Mufasa API": MUFASA_API_URL,
    "OpenVoice API": OPENVOICE_API_URL,
    "App Base": APP_BASE_URL,
    "WebSocket": WS_BASE_URL,
    Mode: ENV.mode,
  });
  console.groupEnd();
}
