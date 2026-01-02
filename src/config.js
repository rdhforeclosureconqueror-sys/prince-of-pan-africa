// ✅ src/config.js
// Centralized configuration for all frontend API + WebSocket connections

// Primary API Base
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://api.simbawaujamaa.com";

// Alias (some older files may import API_BASE instead)
export const API_BASE = API_BASE_URL;

// Frontend base URL
export const APP_BASE_URL =
  import.meta.env.VITE_APP_BASE_URL || "https://simbawaujamaa.com";

// WebSocket URL (for live updates)
export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL || "wss://api.simbawaujamaa.com";

// You can log it in dev mode to confirm
if (import.meta.env.DEV) {
  console.log("✅ Config loaded:", { API_BASE_URL, APP_BASE_URL, WS_BASE_URL });
}
