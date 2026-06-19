import { api } from "./api";

export async function getAssessmentCatalog() {
  return api("/member/assessments/catalog", { method: "GET" });
}

export async function getArchetypeCatalog() {
  return api("/member/assessments/archetypes", { method: "GET" });
}

export async function createAssessmentTransferToken(redirectAssessment, destination = "assessment") {
  return api("/member/assessments/transfer-token", {
    method: "POST",
    body: JSON.stringify({ redirect_assessment: redirectAssessment || null, destination }),
  });
}

export async function getAssessmentResults() {
  return api("/member/assessments/results", { method: "GET" });
}

export async function getAssessmentResult(resultId) {
  return api(`/member/assessments/results/${encodeURIComponent(resultId)}`, { method: "GET" });
}

export async function getGrowthProfile() {
  return api("/member/assessments/growth-profile", { method: "GET" });
}
