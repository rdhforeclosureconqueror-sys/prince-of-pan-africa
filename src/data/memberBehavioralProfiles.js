// Deprecated: these static profiles are fallback-only. New intelligence features should
// prefer backend-generated Member Intelligence read models when live society data exists.
export const memberBehavioralProfilesStatus = "deprecated_fallback_only";

export const sampleMemberBehavioralProfiles = Object.freeze([
  {
    key: "amina-johnson",
    displayName: "Amina Johnson",
    behavioralConfidence: "High",
    primaryArchetypes: ["Documentation Steward", "Grounded Operator"],
    secondaryArchetypes: ["Circle Keeper"],
    demonstratedStrengths: ["Consistency", "Documentation", "Reliability", "Calm decision making", "Service orientation"],
    completedAssessments: [
      {
        name: "Leadership archetype assessment",
        interpretation: "Leadership Assessment indicates collaborative leadership and a preference for shared accountability.",
        traits: ["accountability", "strategic focus", "delegation", "service leadership", "decision clarity"],
      },
      {
        name: "Operations and follow-through assessment",
        interpretation: "Operations Assessment indicates steady follow-through, practical planning, and task ownership.",
        traits: ["follow-through", "planning", "prioritization", "coordination", "dependability", "consistency"],
      },
      {
        name: "Documentation and knowledge stewardship assessment",
        interpretation: "Documentation Assessment indicates careful records, plain-language summaries, and strong information stewardship.",
        traits: ["documentation", "accuracy", "plain-language reporting", "structure", "attention to detail", "confidentiality"],
      },
    ],
  },
  {
    key: "malik-thompson",
    displayName: "Malik Thompson",
    behavioralConfidence: "Medium",
    primaryArchetypes: ["Community Connector", "Care Weaver"],
    secondaryArchetypes: ["Empathic Listener"],
    demonstratedStrengths: ["Service orientation", "Active listening", "Relationship building", "Encouragement", "Reliability"],
    completedAssessments: [
      {
        name: "Care capacity and boundaries assessment",
        interpretation: "Care Assessment indicates compassion, boundary awareness, and consistent follow-up with members.",
        traits: ["compassion", "boundary setting", "follow-through", "patience", "confidentiality", "care ethics"],
      },
      {
        name: "Communication and facilitation assessment",
        interpretation: "Communication Assessment indicates clear information sharing and a welcoming tone.",
        traits: ["active listening", "clear expectations", "welcoming presence", "plain language", "encouragement", "responsiveness"],
      },
    ],
  },
  {
    key: "nia-carter",
    displayName: "Nia Carter",
    behavioralConfidence: "Preliminary",
    primaryArchetypes: ["Resource Guardian"],
    secondaryArchetypes: ["Systems Steward"],
    demonstratedStrengths: ["Financial care", "Risk awareness", "Careful review", "Transparency"],
    completedAssessments: [
      {
        name: "Treasury stewardship assessment",
        interpretation: "Treasury Assessment indicates financial discipline, risk awareness, and respect for transparent records.",
        traits: ["financial discipline", "accuracy", "transparency", "risk awareness", "careful review", "confidentiality"],
      },
    ],
  },
]);

export function getAllSampleMemberBehavioralProfiles() {
  return sampleMemberBehavioralProfiles;
}

export function getSampleMemberBehavioralProfileByKey(key) {
  return sampleMemberBehavioralProfiles.find((profile) => profile.key === key) || null;
}
