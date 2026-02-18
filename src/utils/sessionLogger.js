// ✅ src/utils/sessionLogger.js
// Handles user activity logs for fitness + coaching sessions
// Logs are stored locally (in IndexedDB or localStorage) and synced to your backend API.
// Automatically purges logs older than 7 days to keep the DB lean.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://api.simbawaujamaa.com";
const LOG_KEY = "mufasa_session_logs";

// Helper: load logs from localStorage
function loadLogs() {
  try {
    const data = localStorage.getItem(LOG_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

// Helper: save logs
function saveLogs(logs) {
  localStorage.setItem(LOG_KEY, JSON.stringify(logs));
}

// Helper: clean logs older than 7 days
function purgeOldLogs() {
  const logs = loadLogs();
  const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000; // 7 days
  const fresh = logs.filter((l) => l.timestamp > cutoff);
  saveLogs(fresh);
  return fresh.length !== logs.length;
}

// Helper: send logs to backend
async function syncLogs() {
  const logs = loadLogs();
  if (!logs.length) return;

  try {
    await fetch(`${API_BASE}/fitness/session-log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "omit",
      body: JSON.stringify({ logs }),
    });

    // Clear after successful sync
    localStorage.removeItem(LOG_KEY);
  } catch (err) {
    console.warn("⚠️ Session log sync failed:", err);
  }
}

// Main: start tracking activity + clean up schedule
export function initSessionLogger() {
  console.log("🦁 Session Logger active.");

  // Clean up old logs
  purgeOldLogs();

  // Capture key events (AI responses, corrections, etc.)
  window.addEventListener("mufasa:log", (e) => {
    const logs = loadLogs();
    const entry = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      type: e.detail?.type || "event",
      data: e.detail?.data || {},
    };
    logs.push(entry);
    saveLogs(logs);
  });

  // Sync logs every 2 minutes while app is open
  setInterval(syncLogs, 2 * 60 * 1000);

  // Final sync before leaving page
  window.addEventListener("beforeunload", syncLogs);
}
