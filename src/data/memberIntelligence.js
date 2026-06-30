import { getSampleMemberBehavioralProfileByKey, sampleMemberBehavioralProfiles } from "./memberBehavioralProfiles.js";

const REQUIRED_ASSESSMENTS = [
  "Leadership archetype assessment",
  "Operations and follow-through assessment",
  "Care capacity and boundaries assessment",
  "Treasury stewardship assessment",
  "Communication and facilitation assessment",
  "Documentation and knowledge stewardship assessment",
];

function asArray(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  return value ? [value] : [];
}

function normalizeName(value) {
  return String(value || "").trim();
}

function resultName(result) {
  return normalizeName(result?.assessment_name || result?.name || result?.title || result?.assessment || result?.category || "Garvey assessment");
}

function resultLabel(result) {
  const primary = result?.primary_result || result?.archetype || result?.profile || result?.result || null;
  if (typeof primary === "string") return primary;
  return primary?.label || primary?.name || primary?.title || result?.overall_score || result?.label || "Assessment evidence captured";
}

function resultTraits(result) {
  return [
    ...asArray(result?.strengths),
    ...asArray(result?.demonstrated_strengths),
    ...asArray(result?.traits),
    ...asArray(result?.primary_result?.traits),
    ...asArray(result?.archetype?.traits),
  ].map(String);
}

function resultGrowth(result) {
  return [
    ...asArray(result?.opportunities_for_growth),
    ...asArray(result?.development_areas),
    ...asArray(result?.growth_edges),
    ...asArray(result?.recommended_next_steps),
  ].map((item) => (typeof item === "string" ? item : item?.label || item?.value || item?.name)).filter(Boolean);
}

function confidenceFor(completedCount, evidenceCount) {
  if (completedCount >= 4 && evidenceCount >= 8) return "High";
  if (completedCount >= 2 && evidenceCount >= 4) return "Medium";
  if (completedCount >= 1) return "Preliminary";
  return "Fallback";
}

export function buildMemberIntelligence({ member = {}, assessmentResults = [], growthProfile = null, appointments = [], sampleProfileKey = "amina-johnson" } = {}) {
  const liveResults = asArray(assessmentResults).filter((item) => item && (item.completed_at || item.completion_date || item.primary_result || item.archetype || item.strengths || item.assessment_name));
  if (!liveResults.length) {
    const fallbackProfile = getSampleMemberBehavioralProfileByKey(sampleProfileKey) || sampleMemberBehavioralProfiles[0];
    return memberIntelligenceFromSample(fallbackProfile, "No completed assessment evidence was available for this member.");
  }

  const completedAssessments = liveResults.map((result) => ({
    name: resultName(result),
    interpretation: `${resultName(result)} indicates ${resultLabel(result)}.`,
    traits: resultTraits(result),
    evidenceSource: result?.id || result?.result_id || result?.assessment_id || resultName(result),
    completedAt: result?.completed_at || result?.completion_date || result?.created_at || null,
  }));
  const completedNames = completedAssessments.map((item) => item.name.toLowerCase());
  const missingAssessments = REQUIRED_ASSESSMENTS.filter((name) => !completedNames.includes(name.toLowerCase()));
  const strengths = [...new Set(liveResults.flatMap(resultTraits))];
  const developmentAreas = [...new Set(liveResults.flatMap(resultGrowth))];
  const consideredRoles = asArray(growthProfile?.recommended_roles || growthProfile?.role_recommendations || liveResults.flatMap((result) => asArray(result?.recommended_roles))).map((role) => typeof role === "string" ? { roleName: role } : role);
  const evidence = completedAssessments.map((assessment) => ({ source: assessment.evidenceSource, summary: assessment.interpretation, traits: assessment.traits }));
  const confidence = confidenceFor(completedAssessments.length, strengths.length + evidence.length);

  return {
    source: "live_member_intelligence",
    isFallback: false,
    fallbackReason: null,
    memberId: member.id || member.email || member.name || "current-member",
    displayName: member.name || member.display_name || member.email || "Member",
    behavioralConfidence: confidence,
    completedAssessments,
    missingAssessments,
    behavioralStrengths: strengths,
    developmentAreas,
    consideredRoles,
    pastAppointments: appointments,
    roleAppointmentHistory: appointments,
    confidence,
    confidenceCalculation: `${completedAssessments.length} completed assessment(s), ${strengths.length} strength signal(s), ${missingAssessments.length} missing assessment(s).`,
    evidence,
    suggestedNextAssessment: missingAssessments[0] || growthProfile?.summary?.recommended_next_assessment?.assessment_name || "Continue periodic reassessment",
    raw: { member, assessmentResults: liveResults, growthProfile, appointments },
  };
}

export function memberIntelligenceFromSample(profile, fallbackReason = "Live intelligence unavailable.") {
  const evidence = (profile.completedAssessments || []).map((assessment) => ({ source: `sample:${assessment.name}`, summary: assessment.interpretation, traits: assessment.traits || [] }));
  return {
    ...profile,
    source: "deprecated_sample_profile",
    isFallback: true,
    fallbackReason,
    memberId: profile.key,
    confidence: profile.behavioralConfidence,
    behavioralStrengths: profile.demonstratedStrengths || [],
    developmentAreas: [],
    missingAssessments: [],
    consideredRoles: [],
    pastAppointments: [],
    roleAppointmentHistory: [],
    evidence,
    confidenceCalculation: `Deprecated fallback profile with ${evidence.length} sample assessment(s).`,
    suggestedNextAssessment: "Complete a live Garvey assessment",
    raw: profile,
  };
}

export function memberIntelligenceToBehavioralProfile(intelligence) {
  if (!intelligence) return null;
  return {
    key: intelligence.memberId,
    displayName: intelligence.displayName,
    behavioralConfidence: intelligence.confidence || intelligence.behavioralConfidence,
    primaryArchetypes: asArray(intelligence.primaryArchetypes || intelligence.consideredRoles?.map((role) => role.roleName || role.name)).slice(0, 3),
    secondaryArchetypes: asArray(intelligence.secondaryArchetypes),
    demonstratedStrengths: intelligence.behavioralStrengths || intelligence.demonstratedStrengths || [],
    completedAssessments: intelligence.completedAssessments || [],
    missingAssessments: intelligence.missingAssessments || [],
    developmentAreas: intelligence.developmentAreas || [],
    consideredRoles: intelligence.consideredRoles || [],
    pastAppointments: intelligence.pastAppointments || [],
    roleAppointmentHistory: intelligence.roleAppointmentHistory || [],
    confidence: intelligence.confidence,
    evidence: intelligence.evidence || [],
    source: intelligence.source,
    isFallback: intelligence.isFallback,
    fallbackReason: intelligence.fallbackReason,
    confidenceCalculation: intelligence.confidenceCalculation,
    suggestedNextAssessment: intelligence.suggestedNextAssessment,
    rawMemberIntelligence: intelligence,
  };
}

export const manualAdminMemberIntelligenceChecklist = [
  "Open an existing member — Member Intelligence loads.",
  "Open a member with no assessments — Fallback profile appears with warning.",
  "Complete an assessment and refresh — Live intelligence replaces fallback.",
  "Open Role Interpretation — Evidence section explains recommendation.",
  "Open First Ten — Role consideration uses live intelligence.",
  "Open Leadership Review — Confidence and missing assessments appear.",
  "Verify no role is automatically assigned.",
  "Verify existing Society Builder workflows still function.",
];
