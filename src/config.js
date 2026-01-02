// src/config.js
// ✅ Centralized environment configuration for frontend

// Backend API base URL — change this if you’re testing locally
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://api.simbawaujamaa.com";

// Frontend app base URL
export const APP_BASE_URL =
  import.meta.env.VITE_APP_BASE_URL || "https://simbawaujamaa.com";

// Optional WebSocket URL (auto-fallback)
export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL || "wss://api.simbawaujamaa.com";
