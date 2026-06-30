import { getRoleBlueprintByKey } from "./mutualAidRoleBlueprints.js";

const ASSESSMENT_IMPORTANCE = {
  "Leadership archetype assessment": "leadership style, responsibility holding, and shared accountability",
  "Operations and follow-through assessment": "follow-through, coordination, and practical task ownership",
  "Care capacity and boundaries assessment": "care ethics, confidentiality, boundaries, and support follow-up",
  "Treasury stewardship assessment": "transparent financial stewardship and careful controls",
  "Communication and facilitation assessment": "clear information sharing, meeting participation, and member-facing communication",
  "Conflict style and repair assessment": "repair, de-escalation, fairness, and hard-conversation readiness",
  "Documentation and knowledge stewardship assessment": "usable records, privacy care, and continuity of knowledge",
  "Preparedness readiness assessment": "calm readiness, emergency planning, and safety-oriented action",
  "Technology confidence assessment": "safe tool use, access support, and workflow documentation",
  "Community organizing assessment": "relationship building, outreach, and clear community asks",
};

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

function completedAssessmentNames(profile) {
  return (profile.completedAssessments || []).map((assessment) => assessment.name);
}

function missingAssessmentNames(profile, blueprint) {
  const completedNames = completedAssessmentNames(profile);
  const explicitlyMissing = profile.missingAssessments || [];
  return unique([
    ...blueprint.recommendedAssessments.filter((name) => !completedNames.includes(name)),
    ...explicitlyMissing.filter((name) => blueprint.recommendedAssessments.includes(name)),
  ]);
}

function matchingTraitEvidence(profile, blueprint) {
  const needs = [
    ...blueprint.requiredBehavioralTraits,
    ...blueprint.supportingTraits,
    ...blueprint.trustNeeds,
    ...blueprint.reliabilityNeeds,
    ...blueprint.communicationNeeds,
    ...blueprint.conflictNeeds,
    ...blueprint.documentationNeeds,
    ...blueprint.decisionMakingNeeds,
    ...blueprint.stressToleranceNeeds,
  ].map(normalize);

  return (profile.completedAssessments || []).map((assessment) => {
    const matchingTraits = (assessment.traits || []).filter((trait) => {
      const normalizedTrait = normalize(trait);
      return needs.some((need) => need.includes(normalizedTrait) || normalizedTrait.includes(need));
    });
    return { assessmentName: assessment.name, interpretation: assessment.interpretation, matchingTraits };
  }).filter((item) => item.matchingTraits.length || item.interpretation);
}

function archetypeMatches(profile, blueprint) {
  const memberArchetypes = [...(profile.primaryArchetypes || []), ...(profile.secondaryArchetypes || [])].map(normalize);
  return blueprint.bestFitArchetypes.filter((archetype) => memberArchetypes.includes(normalize(archetype)));
}

function alignmentLabel(evidenceCount, missingCount, archetypeCount) {
  if (evidenceCount >= 3 && missingCount === 0 && archetypeCount > 0) return "Strong Alignment";
  if (evidenceCount >= 2 && missingCount <= 1) return "Good Alignment";
  if (evidenceCount >= 1) return "Emerging Alignment";
  return "Limited Evidence";
}

function confidenceFor(profile, missingAssessments, evidenceCount) {
  if (profile.behavioralConfidence === "High" && missingAssessments.length === 0 && evidenceCount >= 2) return "High";
  if (profile.behavioralConfidence === "Preliminary" || evidenceCount <= 1) return "Preliminary";
  return "Medium";
}

export function interpretMemberRoleAlignment(profile, roleKey) {
  const blueprint = getRoleBlueprintByKey(roleKey);
  if (!profile || !blueprint) return null;

  const missingAssessments = missingAssessmentNames(profile, blueprint);
  const evidence = matchingTraitEvidence(profile, blueprint);
  const archetypes = archetypeMatches(profile, blueprint);
  const overallAlignment = alignmentLabel(evidence.length, missingAssessments.length, archetypes.length);
  const confidence = confidenceFor(profile, missingAssessments, evidence.length);

  const strengthPool = unique([
    ...(profile.behavioralStrengths || profile.demonstratedStrengths || []),
    ...evidence.flatMap((item) => item.matchingTraits.map((trait) => trait.replace(/\b\w/g, (letter) => letter.toUpperCase()))),
  ]).slice(0, 7);

  const growthAreas = unique([
    ...blueprint.requiredBehavioralTraits,
    ...blueprint.supportingTraits,
  ].filter((trait) => !strengthPool.map(normalize).includes(normalize(trait)))).slice(0, 5);

  const growthPath = unique([
    ...missingAssessments.map((name) => `Complete ${name}`),
    ...blueprint.growthRecommendations,
    `Review handbook guidance for ${blueprint.displayName}.`,
  ]).slice(0, 7);

  return {
    memberName: profile.displayName,
    roleName: blueprint.displayName,
    rolePurpose: blueprint.purpose,
    overallAlignment,
    whyThisAlignmentExists: evidence.map((item) => item.interpretation),
    archetypeInterpretation: archetypes.length
      ? `${profile.displayName}'s ${archetypes.join(" and ")} pattern appears connected to this role blueprint.`
      : `${profile.displayName}'s current archetype evidence can still be interpreted alongside completed assessments; no automatic role conclusion is made.`,
    strengthsAlreadyDemonstrated: strengthPool,
    behavioralStrengths: profile.behavioralStrengths || strengthPool,
    developmentAreas: profile.developmentAreas || [],
    consideredRoles: profile.consideredRoles || [],
    pastAppointments: profile.pastAppointments || [],
    roleAppointmentHistory: profile.roleAppointmentHistory || [],
    evidenceSources: profile.evidence || evidence,
    areasThatCouldBeStrengthened: growthAreas.map((area) => `To become even stronger in this responsibility, consider developing ${area}.`),
    missingAssessmentEvidence: missingAssessments.map((name) => ({
      name,
      reason: `${name} would improve confidence because it reflects ${ASSESSMENT_IMPORTANCE[name] || "behavioral evidence connected to this responsibility"}.`,
    })),
    suggestedGrowthPath: growthPath,
    handbookConnections: blueprint.handbookConnectionPoints,
    complementaryTeamMembers: blueprint.complementaryTeammateTypes,
    confidence,
    confidenceExplanation: missingAssessments.length
      ? "Additional assessment evidence would improve confidence because one or more recommended assessments are not yet complete."
      : "Confidence reflects completed assessment evidence currently available for this role blueprint.",
    missingInformation: missingAssessments.length ? missingAssessments : ["No missing role assessment evidence identified."],
    suggestedNextAssessment: missingAssessments[0] || profile.suggestedNextAssessment || "Continue periodic reassessment",
    communityDecisionReminder: "This report interprets evidence for community review. It does not rank members, appoint members, or replace the community decision process.",
  };
}
