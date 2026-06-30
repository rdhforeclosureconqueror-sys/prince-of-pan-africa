/**
 * @typedef {"chapter-5"|"chapter-8"|"chapter-11"|"chapter-13"|"chapter-14-15"|"chapter-21"|"chapter-22"|"chapter-23"} HandbookChapterKey
 *
 * @typedef {Object} RoleBlueprint
 * @property {string} key
 * @property {string} displayName
 * @property {string} purpose
 * @property {string[]} coreResponsibilities
 * @property {string[]} bestFitArchetypes
 * @property {string[]} helpfulArchetypeCombinations
 * @property {string[]} requiredBehavioralTraits
 * @property {string[]} supportingTraits
 * @property {string[]} trustNeeds
 * @property {string[]} reliabilityNeeds
 * @property {string[]} communicationNeeds
 * @property {string[]} conflictNeeds
 * @property {string[]} documentationNeeds
 * @property {string[]} decisionMakingNeeds
 * @property {string[]} stressToleranceNeeds
 * @property {string[]} recommendedAssessments
 * @property {string} missingAssessmentPromptText
 * @property {string[]} growthRecommendations
 * @property {string[]} complementaryTeammateTypes
 * @property {{chapterKey: HandbookChapterKey, chapterLabel: string, connection: string}[]} handbookConnectionPoints
 */

export const HANDBOOK_CHAPTERS = {
  "chapter-5": "Chapter 5: Name Your First Ten",
  "chapter-8": "Chapter 8: Set the Treasury",
  "chapter-11": "Chapter 11: Create Care Teams",
  "chapter-13": "Chapter 13: Hold the First Meeting",
  "chapter-14-15": "Chapter 14–15: 100-Day Planner",
  "chapter-21": "Chapter 21: Day 100 Report",
  "chapter-22": "Chapter 22: Recommitment",
  "chapter-23": "Chapter 23: Next Phase Planner",
};

const ASSESSMENTS = {
  leadership: "Leadership archetype assessment",
  operations: "Operations and follow-through assessment",
  care: "Care capacity and boundaries assessment",
  finance: "Treasury stewardship assessment",
  communication: "Communication and facilitation assessment",
  conflict: "Conflict style and repair assessment",
  documentation: "Documentation and knowledge stewardship assessment",
  preparedness: "Preparedness readiness assessment",
  technical: "Technology confidence assessment",
  organizing: "Community organizing assessment",
};

const ROLE_SPECS = [
  ["founder-admin", "Founder/Admin", "Hold founding vision, legal/operational stewardship, and accountable launch coordination.", ["Define society purpose and standards", "Convene initial leadership circle", "Maintain governance boundaries", "Coordinate phase planning"], ["Visionary Builder", "Systems Steward"], ["Visionary Builder + Grounded Operator", "Community Connector + Documentation Steward"], ["integrity", "strategic focus", "accountability", "boundary setting"], ["humility", "pattern recognition", "delegation"], ["chapter-5", "chapter-13", "chapter-14-15", "chapter-22", "chapter-23"], [ASSESSMENTS.leadership, ASSESSMENTS.operations, ASSESSMENTS.conflict]],
  ["facilitator", "Facilitator", "Guide meetings so members are heard, decisions are clear, and next steps are owned.", ["Prepare meeting flow", "Hold inclusive discussion", "Track decisions and next actions", "Protect group agreements"], ["Circle Keeper", "Community Connector"], ["Circle Keeper + Documentation Steward", "Empathic Listener + Grounded Operator"], ["active listening", "neutrality", "time stewardship", "group awareness"], ["warmth", "clarifying questions", "calm presence"], ["chapter-13", "chapter-14-15", "chapter-22"], [ASSESSMENTS.communication, ASSESSMENTS.conflict]],
  ["treasurer", "Treasurer", "Safeguard society funds with transparent records, controls, and member-readable reporting.", ["Maintain treasury records", "Prepare financial reports", "Support budget decisions", "Coordinate dual-control practices"], ["Systems Steward", "Resource Guardian"], ["Resource Guardian + Documentation Steward", "Grounded Operator + Circle Keeper"], ["accuracy", "confidentiality", "financial discipline", "transparency"], ["patience", "risk awareness", "plain-language reporting"], ["chapter-8", "chapter-21", "chapter-22"], [ASSESSMENTS.finance, ASSESSMENTS.documentation]],
  ["assistant-treasurer", "Assistant Treasurer", "Back up treasury work and strengthen checks, continuity, and shared financial understanding.", ["Reconcile records", "Verify receipts", "Support reports", "Provide backup coverage"], ["Resource Guardian", "Grounded Operator"], ["Resource Guardian + Systems Steward", "Documentation Steward + Community Connector"], ["accuracy", "dependability", "confidentiality", "procedural discipline"], ["teachability", "careful review", "consistency"], ["chapter-8", "chapter-21"], [ASSESSMENTS.finance, ASSESSMENTS.operations]],
  ["recordkeeper", "Recordkeeper", "Preserve meeting decisions, attendance, agreements, and action history in usable records.", ["Capture minutes", "Maintain decision logs", "Archive attendance and motions", "Share approved summaries"], ["Documentation Steward", "Systems Steward"], ["Documentation Steward + Circle Keeper", "Grounded Operator + Historian"], ["accuracy", "discretion", "consistency", "attention to detail"], ["organization", "follow-up", "plain language"], ["chapter-13", "chapter-21"], [ASSESSMENTS.documentation, ASSESSMENTS.communication]],
  ["care-coordinator", "Care Coordinator", "Coordinate care teams that respond to member needs with dignity, boundaries, and follow-through.", ["Map care needs", "Coordinate care team assignments", "Follow up on support", "Escalate urgent concerns"], ["Empathic Listener", "Care Weaver"], ["Care Weaver + Grounded Operator", "Empathic Listener + Resource Guardian"], ["compassion", "confidentiality", "boundary setting", "follow-through"], ["trauma awareness", "resourcefulness", "patience"], ["chapter-11", "chapter-14-15", "chapter-21"], [ASSESSMENTS.care, ASSESSMENTS.conflict]],
  ["business-liaison", "Business Liaison", "Build reciprocal relationships with local businesses and economic partners.", ["Identify aligned businesses", "Coordinate partnership asks", "Track commitments", "Report opportunities"], ["Community Connector", "Resource Mobilizer"], ["Resource Mobilizer + Systems Steward", "Community Connector + Communications Lead"], ["professionalism", "reciprocity", "clear asks", "follow-through"], ["networking", "negotiation", "gratitude"], ["chapter-5", "chapter-14-15", "chapter-23"], [ASSESSMENTS.organizing, ASSESSMENTS.communication]],
  ["property-liaison", "Property Liaison", "Coordinate stewardship conversations around land, facilities, housing, and shared property needs.", ["Map property needs", "Coordinate site conversations", "Track maintenance concerns", "Support stewardship planning"], ["Stewardship Builder", "Systems Steward"], ["Stewardship Builder + Resource Guardian", "Grounded Operator + Community Connector"], ["practical judgment", "stewardship ethics", "risk awareness", "follow-through"], ["inspection mindset", "patience", "vendor coordination"], ["chapter-14-15", "chapter-23"], [ASSESSMENTS.operations, ASSESSMENTS.organizing]],
  ["youth-liaison", "Youth Liaison", "Represent youth needs and coordinate safe, empowering youth participation.", ["Listen to youth priorities", "Coordinate youth-safe activities", "Connect mentors", "Report youth concerns"], ["Mentor", "Community Connector"], ["Mentor + Care Weaver", "Teacher + Circle Keeper"], ["youth respect", "safety awareness", "encouragement", "reliability"], ["creativity", "patience", "intergenerational listening"], ["chapter-5", "chapter-11", "chapter-14-15"], [ASSESSMENTS.care, ASSESSMENTS.communication]],
  ["preparedness-lead", "Preparedness Lead", "Help the society prepare for emergencies through plans, supplies, drills, and neighborhood readiness.", ["Assess preparedness gaps", "Coordinate drills", "Track supplies", "Create emergency checklists"], ["Preparedness Guardian", "Grounded Operator"], ["Preparedness Guardian + Care Weaver", "Systems Steward + Neighborhood Captain"], ["calm under pressure", "planning discipline", "risk awareness", "decisiveness"], ["teaching", "logistics", "situational awareness"], ["chapter-14-15", "chapter-23"], [ASSESSMENTS.preparedness, ASSESSMENTS.operations]],
  ["elder-liaison", "Elder Liaison", "Ensure elders are respected, heard, protected, and included in care and decision rhythms.", ["Check in with elders", "Surface accessibility needs", "Coordinate elder support", "Preserve elder guidance"], ["Elder Steward", "Empathic Listener"], ["Elder Steward + Historian", "Care Weaver + Transportation Coordinator"], ["respect", "patience", "confidentiality", "consistency"], ["accessibility awareness", "gentleness", "advocacy"], ["chapter-5", "chapter-11", "chapter-22"], [ASSESSMENTS.care, ASSESSMENTS.communication]],
  ["member", "Member", "Participate in the society through dues, care, meetings, accountability, and shared work.", ["Attend core meetings", "Contribute dues or service", "Honor agreements", "Support care and projects"], ["Community Root", "Reliable Contributor"], ["Reliable Contributor + Empathic Listener", "Community Root + Grounded Operator"], ["participation", "honesty", "mutual respect", "dependability"], ["curiosity", "service mindset", "neighborliness"], ["chapter-5", "chapter-13", "chapter-22"], [ASSESSMENTS.leadership, ASSESSMENTS.care]],
  ["supporter", "Supporter", "Offer aligned help without holding core governance authority or automatic role appointment.", ["Provide occasional support", "Share resources", "Respect society boundaries", "Respond to specific requests"], ["Resource Ally", "Community Connector"], ["Resource Ally + Communications Lead", "Mentor + Fundraising Lead"], ["respect for boundaries", "generosity", "clarity", "reliability"], ["availability", "humility", "responsiveness"], ["chapter-5", "chapter-14-15"], [ASSESSMENTS.communication]],
  ["society-coordinator", "Society Coordinator", "Coordinate cross-role execution so the society’s plans move without replacing member governance.", ["Track cross-team work", "Coordinate calendars", "Surface blockers", "Prepare status updates"], ["Grounded Operator", "Systems Steward"], ["Grounded Operator + Circle Keeper", "Systems Steward + Documentation Steward"], ["coordination", "follow-through", "prioritization", "service leadership"], ["calendar discipline", "diplomacy", "pattern tracking"], ["chapter-14-15", "chapter-21", "chapter-23"], [ASSESSMENTS.operations, ASSESSMENTS.leadership]],
  ["membership-coordinator", "Membership Coordinator", "Welcome, orient, and track members while protecting belonging and accountability.", ["Coordinate onboarding", "Maintain membership roster", "Track recommitments", "Answer membership questions"], ["Community Connector", "Documentation Steward"], ["Community Connector + Circle Keeper", "Documentation Steward + Care Weaver"], ["welcoming presence", "accuracy", "confidentiality", "follow-up"], ["orientation skills", "patience", "encouragement"], ["chapter-5", "chapter-13", "chapter-22"], [ASSESSMENTS.communication, ASSESSMENTS.documentation]],
  ["conflict-mediator", "Conflict Mediator", "Support repair, accountability, and de-escalation when disagreements threaten trust.", ["Receive conflict concerns", "Facilitate repair conversations", "Clarify agreements", "Recommend escalation when needed"], ["Peace Weaver", "Circle Keeper"], ["Peace Weaver + Elder Steward", "Circle Keeper + Documentation Steward"], ["neutrality", "emotional regulation", "fairness", "confidentiality"], ["deep listening", "discernment", "courage"], ["chapter-13", "chapter-22"], [ASSESSMENTS.conflict, ASSESSMENTS.communication]],
  ["volunteer-coordinator", "Volunteer Coordinator", "Match willing helpers to tasks, shifts, and service needs with clear expectations.", ["Recruit volunteers", "Schedule shifts", "Confirm task readiness", "Thank and retain helpers"], ["Community Connector", "Grounded Operator"], ["Community Connector + Resource Mobilizer", "Grounded Operator + Care Weaver"], ["responsiveness", "organization", "encouragement", "clear expectations"], ["gratitude", "flexibility", "people awareness"], ["chapter-14-15", "chapter-21"], [ASSESSMENTS.operations, ASSESSMENTS.communication]],
  ["project-manager", "Project Manager", "Turn approved society priorities into scoped plans, owners, timelines, and delivery checkpoints.", ["Define project scope", "Track milestones", "Coordinate owners", "Report risks and completion"], ["Grounded Operator", "Systems Steward"], ["Grounded Operator + Resource Guardian", "Systems Steward + Communications Lead"], ["planning", "accountability", "risk tracking", "decision clarity"], ["adaptability", "delegation", "status reporting"], ["chapter-14-15", "chapter-21", "chapter-23"], [ASSESSMENTS.operations, ASSESSMENTS.leadership]],
  ["community-organizer", "Community Organizer", "Build community participation around society priorities through outreach and collective action.", ["Map stakeholders", "Recruit participation", "Host outreach conversations", "Coordinate campaigns"], ["Community Connector", "Resource Mobilizer"], ["Community Connector + Circle Keeper", "Resource Mobilizer + Communications Lead"], ["relationship building", "persistence", "clear asks", "cultural respect"], ["storytelling", "canvassing", "coalition awareness"], ["chapter-5", "chapter-13", "chapter-14-15"], [ASSESSMENTS.organizing, ASSESSMENTS.communication]],
  ["communications-lead", "Communications Lead", "Keep members and partners informed with clear, timely, values-aligned messages.", ["Draft announcements", "Maintain communication calendar", "Coordinate channels", "Confirm message accuracy"], ["Storyteller", "Community Connector"], ["Storyteller + Documentation Steward", "Community Connector + Technology Lead"], ["clarity", "timeliness", "accuracy", "tone awareness"], ["editing", "audience awareness", "visual sense"], ["chapter-13", "chapter-14-15", "chapter-21"], [ASSESSMENTS.communication, ASSESSMENTS.documentation]],
  ["technology-lead", "Technology Lead", "Support safe, usable digital tools for member coordination and records access.", ["Maintain tools", "Support user access", "Document workflows", "Flag data risks"], ["Systems Steward", "Technical Steward"], ["Technical Steward + Documentation Steward", "Systems Steward + Communications Lead"], ["security awareness", "patience", "problem solving", "service orientation"], ["training", "accessibility", "troubleshooting"], ["chapter-14-15", "chapter-21"], [ASSESSMENTS.technical, ASSESSMENTS.documentation]],
  ["historian", "Historian", "Preserve the society’s story, lessons, milestones, and elder/member memory.", ["Collect stories", "Capture milestones", "Interview members", "Prepare history summaries"], ["Historian", "Elder Steward"], ["Historian + Archivist", "Elder Steward + Communications Lead"], ["respect", "accuracy", "context awareness", "consent"], ["curiosity", "listening", "narrative skill"], ["chapter-21", "chapter-22", "chapter-23"], [ASSESSMENTS.documentation, ASSESSMENTS.communication]],
  ["archivist", "Archivist", "Organize and protect records so future members can find what matters.", ["Design archive categories", "Store key documents", "Manage retention", "Support retrieval"], ["Documentation Steward", "Archivist"], ["Archivist + Recordkeeper", "Documentation Steward + Technology Lead"], ["organization", "confidentiality", "precision", "stewardship"], ["metadata thinking", "patience", "consistency"], ["chapter-21", "chapter-23"], [ASSESSMENTS.documentation, ASSESSMENTS.technical]],
  ["teacher", "Teacher", "Help members learn practical skills, society practices, and shared political/economic education.", ["Prepare lessons", "Facilitate learning circles", "Adapt to learner needs", "Share learning materials"], ["Teacher", "Circle Keeper"], ["Teacher + Mentor", "Circle Keeper + Documentation Steward"], ["clarity", "patience", "preparation", "learner respect"], ["curriculum design", "encouragement", "reflection"], ["chapter-13", "chapter-14-15", "chapter-22"], [ASSESSMENTS.communication, ASSESSMENTS.leadership]],
  ["mentor", "Mentor", "Offer guidance, encouragement, and skill transfer while respecting member agency.", ["Meet with mentees", "Share experience", "Support goal setting", "Refer needs appropriately"], ["Mentor", "Elder Steward"], ["Mentor + Teacher", "Elder Steward + Care Weaver"], ["patience", "encouragement", "boundaries", "trustworthiness"], ["wisdom sharing", "listening", "consistency"], ["chapter-5", "chapter-11", "chapter-22"], [ASSESSMENTS.care, ASSESSMENTS.communication]],
  ["health-and-wellness-leader", "Health and Wellness Leader", "Coordinate wellness practices and health education without replacing licensed care.", ["Share wellness resources", "Coordinate wellness check-ins", "Promote prevention", "Refer urgent needs"], ["Care Weaver", "Wellness Steward"], ["Wellness Steward + Preparedness Guardian", "Care Weaver + Teacher"], ["care ethics", "boundary setting", "confidentiality", "safety awareness"], ["encouragement", "resource mapping", "body awareness"], ["chapter-11", "chapter-14-15"], [ASSESSMENTS.care, ASSESSMENTS.preparedness]],
  ["event-coordinator", "Event Coordinator", "Plan gatherings that are purposeful, welcoming, accessible, and well-run.", ["Plan event logistics", "Coordinate volunteers", "Manage run-of-show", "Collect feedback"], ["Grounded Operator", "Community Connector"], ["Grounded Operator + Communications Lead", "Community Connector + Volunteer Coordinator"], ["logistics", "hospitality", "time management", "contingency planning"], ["creativity", "vendor coordination", "calm presence"], ["chapter-13", "chapter-14-15", "chapter-21"], [ASSESSMENTS.operations, ASSESSMENTS.communication]],
  ["fundraising-lead", "Fundraising Lead", "Coordinate ethical fundraising and resource development aligned with society boundaries.", ["Create fundraising plans", "Coordinate donor asks", "Track pledges", "Report outcomes"], ["Resource Mobilizer", "Storyteller"], ["Resource Mobilizer + Treasurer", "Storyteller + Community Organizer"], ["ethical asks", "transparency", "persistence", "relationship care"], ["storytelling", "gratitude", "campaign planning"], ["chapter-8", "chapter-14-15", "chapter-23"], [ASSESSMENTS.organizing, ASSESSMENTS.finance]],
  ["transportation-coordinator", "Transportation Coordinator", "Coordinate rides, delivery routes, and mobility support safely and reliably.", ["Match rides to needs", "Coordinate drivers", "Track route details", "Confirm completion"], ["Grounded Operator", "Care Weaver"], ["Grounded Operator + Neighborhood Captain", "Care Weaver + Technology Lead"], ["punctuality", "safety awareness", "coordination", "confidentiality"], ["route planning", "accessibility", "backup planning"], ["chapter-11", "chapter-14-15"], [ASSESSMENTS.operations, ASSESSMENTS.care]],
  ["food-distribution-coordinator", "Food Distribution Coordinator", "Coordinate food sourcing, packing, storage, and distribution with dignity and safety.", ["Track food needs", "Coordinate sourcing", "Organize distribution", "Monitor food safety"], ["Care Weaver", "Grounded Operator"], ["Care Weaver + Resource Mobilizer", "Grounded Operator + Neighborhood Captain"], ["food safety", "dignity", "organization", "follow-through"], ["inventory thinking", "hospitality", "calm logistics"], ["chapter-11", "chapter-14-15", "chapter-21"], [ASSESSMENTS.care, ASSESSMENTS.operations]],
  ["emergency-response-coordinator", "Emergency Response Coordinator", "Coordinate rapid mutual aid response during urgent events without creating unsupported promises.", ["Maintain response contacts", "Triage urgent needs", "Coordinate immediate support", "Debrief after incidents"], ["Preparedness Guardian", "Grounded Operator"], ["Preparedness Guardian + Care Weaver", "Grounded Operator + Communications Lead"], ["calm under pressure", "triage judgment", "clear communication", "safety discipline"], ["after-action learning", "backup planning", "resource awareness"], ["chapter-11", "chapter-14-15", "chapter-21"], [ASSESSMENTS.preparedness, ASSESSMENTS.operations, ASSESSMENTS.conflict]],
  ["neighborhood-captain", "Neighborhood Captain", "Anchor communication and care coordination for a block, zone, or local cluster.", ["Know local members", "Share updates", "Coordinate neighborhood checks", "Surface local needs"], ["Community Connector", "Preparedness Guardian"], ["Community Connector + Care Weaver", "Preparedness Guardian + Transportation Coordinator"], ["local presence", "responsiveness", "neighborly trust", "follow-through"], ["mapping", "hospitality", "situational awareness"], ["chapter-5", "chapter-11", "chapter-14-15"], [ASSESSMENTS.organizing, ASSESSMENTS.preparedness]],
  ["committee-chair", "Committee Chair", "Guide a committee’s work with clear agendas, member participation, and accountable outcomes.", ["Set agendas", "Coordinate committee members", "Track actions", "Report recommendations"], ["Circle Keeper", "Grounded Operator"], ["Circle Keeper + Project Manager", "Grounded Operator + Documentation Steward"], ["facilitation", "accountability", "role clarity", "follow-through"], ["delegation", "meeting craft", "summary reporting"], ["chapter-13", "chapter-14-15", "chapter-21"], [ASSESSMENTS.leadership, ASSESSMENTS.communication]],
  ["documentation-lead", "Documentation Lead", "Create usable guides, templates, and records that make society operations repeatable.", ["Maintain documentation hub", "Create templates", "Review clarity", "Coordinate record standards"], ["Documentation Steward", "Systems Steward"], ["Documentation Steward + Technology Lead", "Systems Steward + Teacher"], ["clarity", "structure", "accuracy", "consistency"], ["editing", "process mapping", "accessibility"], ["chapter-14-15", "chapter-21", "chapter-23"], [ASSESSMENTS.documentation, ASSESSMENTS.operations]],
  ["training-facilitator", "Training Facilitator", "Prepare members to perform roles and practices with confidence and shared standards.", ["Assess training needs", "Facilitate trainings", "Create practice exercises", "Collect learning feedback"], ["Teacher", "Circle Keeper"], ["Teacher + Documentation Steward", "Circle Keeper + Mentor"], ["preparation", "clarity", "patience", "feedback orientation"], ["curriculum design", "encouragement", "adaptability"], ["chapter-14-15", "chapter-22", "chapter-23"], [ASSESSMENTS.communication, ASSESSMENTS.documentation]],
  ["assessment-facilitator", "Assessment Facilitator", "Help members complete assessments, understand results, and prepare for future role-fit review without assigning roles.", ["Explain assessments", "Support completion", "Protect result privacy", "Summarize readiness gaps"], ["Circle Keeper", "Systems Steward"], ["Circle Keeper + Documentation Steward", "Systems Steward + Conflict Mediator"], ["privacy care", "neutrality", "clarity", "non-coercion"], ["data literacy", "encouragement", "discernment"], ["chapter-5", "chapter-14-15", "chapter-22", "chapter-23"], [ASSESSMENTS.leadership, ASSESSMENTS.communication, ASSESSMENTS.conflict]],
];

const defaultNeeds = {
  trustNeeds: ["Keeps member information appropriately private", "Names limits and conflicts of interest early", "Follows society agreements before personal preference"],
  reliabilityNeeds: ["Responds within agreed time windows", "Completes accepted tasks or renegotiates before deadlines", "Maintains backup coverage for essential duties"],
  communicationNeeds: ["Uses plain language", "Confirms decisions and owners", "Escalates blockers without blame"],
  conflictNeeds: ["Pauses before reacting", "Seeks repair before punishment", "Documents agreements after hard conversations"],
  documentationNeeds: ["Keeps lightweight records future members can understand", "Separates facts, decisions, and opinions", "Stores sensitive notes only where appropriate"],
  decisionMakingNeeds: ["Uses member-approved policy", "Distinguishes recommendations from decisions", "Invites affected voices before irreversible action"],
  stressToleranceNeeds: ["Can slow down during urgency", "Asks for support before overload becomes harm", "Practices after-action reflection"],
};

function buildBlueprint([key, displayName, purpose, responsibilities, archetypes, combos, requiredTraits, supportingTraits, chapters, assessments]) {
  return Object.freeze({
    key,
    displayName,
    purpose,
    coreResponsibilities: responsibilities,
    bestFitArchetypes: archetypes,
    helpfulArchetypeCombinations: combos,
    requiredBehavioralTraits: requiredTraits,
    supportingTraits,
    ...defaultNeeds,
    recommendedAssessments: assessments,
    missingAssessmentPromptText: `Before comparing a member to the ${displayName} blueprint, ask them to complete: ${assessments.join(", ")}.`,
    growthRecommendations: [
      `Shadow an experienced ${displayName} or adjacent role for one planning cycle.`,
      "Practice the role with a low-risk task before holding responsibility alone.",
      "Ask a complementary teammate to review communication, documentation, and follow-through habits.",
    ],
    complementaryTeammateTypes: ["Documentation Steward", "Circle Keeper", "Grounded Operator", "Care Weaver"].filter((type) => !archetypes.includes(type)).slice(0, 3),
    handbookConnectionPoints: chapters.map((chapterKey) => ({
      chapterKey,
      chapterLabel: HANDBOOK_CHAPTERS[chapterKey],
      connection: `${displayName} supports ${HANDBOOK_CHAPTERS[chapterKey]} by turning handbook guidance into accountable society practice.`,
    })),
  });
}

export const mutualAidRoleBlueprints = Object.freeze(ROLE_SPECS.map(buildBlueprint));

export function getAllRoleBlueprints() {
  return mutualAidRoleBlueprints;
}

export function getRoleBlueprintByKey(key) {
  return mutualAidRoleBlueprints.find((role) => role.key === key) || null;
}

export function getRolesByHandbookChapter(chapterKey) {
  return mutualAidRoleBlueprints.filter((role) => role.handbookConnectionPoints.some((point) => point.chapterKey === chapterKey));
}

export function getRecommendedAssessmentsForRole(key) {
  return getRoleBlueprintByKey(key)?.recommendedAssessments || [];
}

export function getGrowthRecommendationsForRole(key) {
  return getRoleBlueprintByKey(key)?.growthRecommendations || [];
}
