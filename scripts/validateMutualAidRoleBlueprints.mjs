import { mutualAidRoleBlueprints } from "../src/data/mutualAidRoleBlueprints.js";

const expectedKeys = [
  "founder-admin", "facilitator", "treasurer", "assistant-treasurer", "recordkeeper", "care-coordinator",
  "business-liaison", "property-liaison", "youth-liaison", "preparedness-lead", "elder-liaison", "member",
  "supporter", "society-coordinator", "membership-coordinator", "conflict-mediator", "volunteer-coordinator",
  "project-manager", "community-organizer", "communications-lead", "technology-lead", "historian", "archivist",
  "teacher", "mentor", "health-and-wellness-leader", "event-coordinator", "fundraising-lead",
  "transportation-coordinator", "food-distribution-coordinator", "emergency-response-coordinator", "neighborhood-captain",
  "committee-chair", "documentation-lead", "training-facilitator", "assessment-facilitator",
];

const requiredFields = [
  "key", "displayName", "purpose", "coreResponsibilities", "bestFitArchetypes", "helpfulArchetypeCombinations",
  "requiredBehavioralTraits", "supportingTraits", "trustNeeds", "reliabilityNeeds", "communicationNeeds", "conflictNeeds",
  "documentationNeeds", "decisionMakingNeeds", "stressToleranceNeeds", "recommendedAssessments", "missingAssessmentPromptText",
  "growthRecommendations", "complementaryTeammateTypes", "handbookConnectionPoints",
];

const errors = [];
const actualKeys = mutualAidRoleBlueprints.map((role) => role.key);
for (const key of expectedKeys) if (!actualKeys.includes(key)) errors.push(`Missing role key: ${key}`);
for (const key of actualKeys) if (!expectedKeys.includes(key)) errors.push(`Unexpected role key: ${key}`);

for (const role of mutualAidRoleBlueprints) {
  for (const field of requiredFields) {
    const value = role[field];
    if (Array.isArray(value) && value.length === 0) errors.push(`${role.key}.${field} is empty`);
    if (!Array.isArray(value) && (value === undefined || value === null || value === "")) errors.push(`${role.key}.${field} is missing`);
  }
  for (const point of role.handbookConnectionPoints || []) {
    if (!point.chapterKey || !point.chapterLabel || !point.connection) errors.push(`${role.key} has incomplete handbook connection`);
  }
}

if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Validated ${mutualAidRoleBlueprints.length} Mutual Aid role blueprints.`);
