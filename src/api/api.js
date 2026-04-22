// src/api/api.js
import { API_BASE_URL } from "../config";

/**
 * Universal API client for Simba Waa Ujamaa
 * Handles JSON + text responses, cookies, and error normalization
 */
export async function api(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const isFormData = options.body instanceof FormData;
  const normalizedHeaders = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      credentials: "include", // ✅ keeps login sessions
      headers: normalizedHeaders,
    });

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : await res.text();

    // ✅ Normalize response and throw for errors
    if (!res.ok) {
      let msg =
        typeof data === "string"
          ? data
          : data?.detail || data?.error || "Unknown server error";

      if (res.status === 422) {
        msg = "Upload failed. Check file type or missing fields.";
      }

      console.error(`❌ API error [${res.status}] on ${url}:`, msg);
      const error = new Error(msg);
      error.status = res.status;
      error.payload = data;
      throw error;
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
