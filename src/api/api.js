// src/api/api.js
import { API_BASE_URL } from "../config";

/**
 * Universal API client for Simba Waa Ujamaa
 * Handles JSON + text responses, cookies, and error normalization
 */
export async function api(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  try {
    const res = await fetch(url, {
      ...options,
      credentials: "include", // ✅ keeps login sessions
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : await res.text();

    // ✅ Normalize response and throw for errors
    if (!res.ok) {
      const msg =
        typeof data === "string"
          ? data
          : data?.error || "Unknown server error";
      console.error(`❌ API error [${res.status}] on ${url}:`, msg);
      throw new Error(msg);
    }

    return data;
  } catch (err) {
    console.error(`🚨 Network/API failure on ${path}:`, err);
    throw err;
  }
}

/**
 * Example helper shortcuts
 * (optional but useful for cleaner calls)
 */
export const get = (path) => api(path);
export const post = (path, body) =>
  api(path, { method: "POST", body: JSON.stringify(body) });
export const put = (path, body) =>
  api(path, { method: "PUT", body: JSON.stringify(body) });
export const del = (path) => api(path, { method: "DELETE" });
