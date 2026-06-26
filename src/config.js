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
const CUSTOM_API_DOMAIN = "api.simbawaujamaa.com";
// Production should use the same-site custom API domain after Render has
// verified DNS and issued the TLS certificate. The Render backend URL remains
// documented as the operational fallback only.
const PROD_API = "https://api.simbawaujamaa.com";
const DEV_API = "http://localhost:3000";
const explicitApiBaseUrl = String(import.meta.env.VITE_API_BASE_URL || "").trim();

export const API_BASE_URL =
  explicitApiBaseUrl ||
  (hostname === "localhost" ? DEV_API : PROD_API);


const runtimeSearchParams = new URLSearchParams(window?.location?.search || "");
const AUTH_DEBUG_FLAG = String(import.meta.env.VITE_AUTH_DEBUG || "").trim().toLowerCase();

export const AUTH_DEBUG =
  ["1", "true", "yes", "on"].includes(AUTH_DEBUG_FLAG) ||
  runtimeSearchParams.get("authDebug") === "1" ||
  window?.localStorage?.getItem("authDebug") === "1";

export const API_DEBUG =
  AUTH_DEBUG || runtimeSearchParams.get("apiDebug") === "1" || window?.localStorage?.getItem("apiDebug") === "1";

if (API_BASE_URL.includes(CUSTOM_API_DOMAIN) && API_DEBUG) {
  console.info(
    `[runtime] ${CUSTOM_API_DOMAIN} is valid for production after Render verifies DNS and certificate for prince-of-pan-africa-backend.`
  );
}

if (API_DEBUG) {
  console.info("[runtime] resolved API_BASE_URL", API_BASE_URL);
}

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
const PROD_WS = API_BASE_URL.replace(/^http/, "ws");
const DEV_WS = "ws://localhost:3000";

export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL ||
  (hostname === "localhost" ? DEV_WS : PROD_WS);

if (WS_BASE_URL.includes(CUSTOM_API_DOMAIN) && API_DEBUG) {
  console.info(
    `[runtime] WebSocket host ${CUSTOM_API_DOMAIN} is valid after Render verifies DNS and certificate for prince-of-pan-africa-backend.`
  );
}

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

const TEXT_BOOK_ORGANIZER_FLAG = import.meta.env.VITE_ENABLE_TEXT_BOOK_ORGANIZER;
const MUTUAL_AID_OVERVIEW_FLAG = import.meta.env.VITE_ENABLE_MUTUAL_AID_OVERVIEW;
const MUTUAL_AID_ADMIN_PLANNING_FLAG = import.meta.env.VITE_ENABLE_MUTUAL_AID_ADMIN_PLANNING;
const MUTUAL_AID_PILOT_UI_SHELL_FLAG = import.meta.env.VITE_ENABLE_MUTUAL_AID_PILOT_UI_SHELL;
const MUTUAL_AID_PILOT_READINESS_SHELL_FLAG = import.meta.env.VITE_ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL;
const MUTUAL_AID_ALLOWLIST_SHELL_FLAG = import.meta.env.VITE_ENABLE_MUTUAL_AID_ALLOWLIST_SHELL;
const normalizedTextBookOrganizerFlag = String(TEXT_BOOK_ORGANIZER_FLAG || "").trim().toLowerCase();
const normalizedMutualAidOverviewFlag = String(MUTUAL_AID_OVERVIEW_FLAG || "").trim().toLowerCase();
const normalizedMutualAidAdminPlanningFlag = String(MUTUAL_AID_ADMIN_PLANNING_FLAG || "").trim().toLowerCase();
const normalizedMutualAidPilotUiShellFlag = String(MUTUAL_AID_PILOT_UI_SHELL_FLAG || "").trim().toLowerCase();
const normalizedMutualAidPilotReadinessShellFlag = String(MUTUAL_AID_PILOT_READINESS_SHELL_FLAG || "").trim().toLowerCase();
const normalizedMutualAidAllowlistShellFlag = String(MUTUAL_AID_ALLOWLIST_SHELL_FLAG || "").trim().toLowerCase();

export const ENABLE_TEXT_BOOK_ORGANIZER = TEXT_BOOK_ORGANIZER_FLAG === undefined
  ? !isDev
  : ["1", "true", "yes", "on"].includes(normalizedTextBookOrganizerFlag);

export const ENABLE_MUTUAL_AID_OVERVIEW = MUTUAL_AID_OVERVIEW_FLAG === undefined
  ? true
  : ["1", "true", "yes", "on"].includes(normalizedMutualAidOverviewFlag);

export const ENABLE_MUTUAL_AID_ADMIN_PLANNING = MUTUAL_AID_ADMIN_PLANNING_FLAG === undefined
  ? false
  : ["1", "true", "yes", "on"].includes(normalizedMutualAidAdminPlanningFlag);

export const ENABLE_MUTUAL_AID_PILOT_UI_SHELL = MUTUAL_AID_PILOT_UI_SHELL_FLAG === undefined
  ? false
  : ["1", "true", "yes", "on"].includes(normalizedMutualAidPilotUiShellFlag);

export const ENABLE_MUTUAL_AID_PILOT_READINESS_SHELL = MUTUAL_AID_PILOT_READINESS_SHELL_FLAG === undefined
  ? false
  : ["1", "true", "yes", "on"].includes(normalizedMutualAidPilotReadinessShellFlag);

export const ENABLE_MUTUAL_AID_ALLOWLIST_SHELL = MUTUAL_AID_ALLOWLIST_SHELL_FLAG === undefined
  ? false
  : ["1", "true", "yes", "on"].includes(normalizedMutualAidAllowlistShellFlag);

export const MUTUAL_AID_ACTIVATION_THRESHOLD = 20000;
export const MUTUAL_AID_CURRENT_PROGRESS = 0;
export const MUTUAL_AID_STATUS = "Building Toward Activation";

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
