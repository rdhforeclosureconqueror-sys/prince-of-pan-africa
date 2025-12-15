// src/api/mufasaClient.js
const API_BASE = import.meta.env.VITE_MUFASA_API;

async function callMufasaAPI(endpoint, payload = {}, method = "POST") {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: method === "POST" ? JSON.stringify(payload) : undefined,
    });

    if (!res.ok) {
      throw new Error(`Mufasa API Error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    return data;
  } catch (error) {
    console.error("❌ API Request Failed:", error);
    return { error: error.message };
  }
}

// --- Chat ---
export async function sendChatMessage(message) {
  return callMufasaAPI("/chat/message", { message });
}

// --- Portal ---
export async function startPortal(portalId) {
  return callMufasaAPI("/portal/start", { portal_id: portalId });
}

export async function continuePortal(portalId, resumeCode, question) {
  return callMufasaAPI("/portal/continue", {
    portal_id: portalId,
    resume_code: resumeCode,
    question,
  });
}

// --- Health ---
export async function checkHealth() {
  return callMufasaAPI("/health", {}, "GET");
}

// --- Info ---
export async function getAPIInfo() {
  return callMufasaAPI("/info", {}, "GET");
}
