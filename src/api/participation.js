import { api } from "./api";

const GUEST_SESSION_KEY = "simba_guest_session";

function getGuestSessionId() {
  if (typeof window === "undefined") return null;
  const existing = window.localStorage?.getItem(GUEST_SESSION_KEY);
  if (existing) return existing;
  const generated = `guest_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  window.localStorage?.setItem(GUEST_SESSION_KEY, generated);
  return generated;
}

export function getStarExperience() {
  const guestSessionId = getGuestSessionId();
  return api("/participation/experience", {
    method: "GET",
    headers: guestSessionId ? { "X-Guest-Session-Id": guestSessionId } : {},
  });
}

export async function recordParticipationActivity(activityType, sourceModule, metadata = {}) {
  const guestSessionId = getGuestSessionId();
  console.info("[participation] activity received", { activityType, sourceModule, guestSessionId, metadata });
  const response = await api("/participation/activity", {
    method: "POST",
    headers: guestSessionId ? { "X-Guest-Session-Id": guestSessionId } : {},
    body: JSON.stringify({ activity_type: activityType, source_module: sourceModule, guest_session_id: guestSessionId, metadata }),
  });
  console.info("[participation] dashboard refresh + notification", response);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("simba:participation-updated", { detail: response }));
  }
  return response;
}

export function getCommunityTrustExperience() {
  return api("/participation/community-trust", { method: "GET" });
}

export function getOpenVerificationRequests() {
  return api("/participation/verification-requests/open", { method: "GET" });
}

export function getRecentCommunityActivity() {
  return api("/participation/community-activity/recent", { method: "GET" });
}
