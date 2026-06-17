import { api } from "./api";

export function getStarExperience() {
  return api("/participation/experience", { method: "GET" });
}

export async function recordParticipationActivity(activityType, sourceModule, metadata = {}) {
  return api("/participation/activity", {
    method: "POST",
    body: JSON.stringify({ activity_type: activityType, source_module: sourceModule, metadata }),
  });
}
