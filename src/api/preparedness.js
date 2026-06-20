import { api } from "./api";

export function getPreparednessSummary() {
  return api("/preparedness/summary", { method: "GET" });
}

export function savePreparednessProfile(payload) {
  return api("/preparedness/household-profile", { method: "PUT", body: JSON.stringify(payload) });
}

export function logPreparednessInventory(payload) {
  return api("/preparedness/inventory", { method: "POST", body: JSON.stringify(payload) });
}

export function savePreparednessVolunteer(payload) {
  return api("/preparedness/volunteer", { method: "PUT", body: JSON.stringify(payload) });
}
