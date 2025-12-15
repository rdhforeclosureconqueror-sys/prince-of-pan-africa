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
  try {
    const res = await fetch(`${import.meta.env.VITE_MUFASA_API}/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`HTTP ${res.status}: ${err}`);
    }

    const data = await res.json();

    // Normalize response fields (some FastAPI routes may return .reply or .response)
    return data.reply || data.response || data.answer || "🦁 Mufasa is silent...";
  } catch (error) {
    console.error("Error talking to Mufasa:", error);
    return "⚠️ Could not reach Mufasa. Check backend connection.";
  }
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
