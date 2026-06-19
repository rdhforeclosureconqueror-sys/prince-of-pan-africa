import { api } from "./api";

export async function getAssessmentCatalog() {
  return api("/member/assessments/catalog", { method: "GET" });
}

export async function createAssessmentTransferToken(redirectAssessment) {
  return api("/member/assessments/transfer-token", {
    method: "POST",
    body: JSON.stringify({ redirect_assessment: redirectAssessment || null }),
  });
}

export async function getAssessmentResults() {
  return api("/member/assessments/results", { method: "GET" });
}
