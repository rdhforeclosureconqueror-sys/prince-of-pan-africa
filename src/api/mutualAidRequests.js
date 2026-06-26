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
