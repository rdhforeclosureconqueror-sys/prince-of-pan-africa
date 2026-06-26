import { get, post } from "./api";

export function saveMutualAidDraft(payload) {
  return post("/mutual-aid/requests/draft", payload);
}

export function submitMutualAidRequest(requestId) {
  return post(`/mutual-aid/requests/${requestId}/submit`, {});
}

export function getMutualAidRequest(requestId) {
  return get(`/mutual-aid/requests/${requestId}`);
}

export function addMutualAidDocumentMetadata(requestId, payload) {
  return post(`/mutual-aid/requests/${requestId}/documents/metadata`, payload);
}

export function getMutualAidAdminRequests() {
  return get("/mutual-aid/admin/requests");
}

export function getMutualAidAdminRequest(requestId) {
  return get(`/mutual-aid/admin/requests/${requestId}`);
}

export function assignMutualAidReviewer(requestId, reviewerUserId) {
  return post(`/mutual-aid/admin/requests/${requestId}/assign-reviewer`, { reviewer_user_id: Number(reviewerUserId) });
}

export function addMutualAidRecommendation(requestId, payload) {
  return post(`/mutual-aid/admin/requests/${requestId}/recommendation`, payload);
}

export function requestMutualAidMoreInfo(requestId, message) {
  return post(`/mutual-aid/admin/requests/${requestId}/request-more-info`, { message });
}

export function discloseMutualAidConflict(requestId, disclosure) {
  return post(`/mutual-aid/admin/requests/${requestId}/conflict-disclosure`, { disclosure });
}
