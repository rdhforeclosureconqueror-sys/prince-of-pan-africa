export const OPERATION_MODULE_STATUSES = {
  available: "Available",
  comingSoon: "Coming Soon",
};

export const OPERATION_MODULE_CATEGORIES = {
  readiness: "Readiness & Response",
  service: "Service & Care",
  food: "Food & Land",
  chapters: "Chapters & Governance",
  economy: "Community Economy",
};

export const COMMUNITY_OPERATION_MODULES = [
  {
    key: "preparedness",
    title: "Community Preparedness",
    description: "Household and community readiness pathways for resilience and coordinated response.",
    route: "/community/preparedness",
    legacyRoutes: ["/preparedness"],
    status: OPERATION_MODULE_STATUSES.available,
    category: OPERATION_MODULE_CATEGORIES.readiness,
    icon: "🛡️",
    memberCta: "Continue Preparedness",
    adminNotes: "First live Community Operations module. Preserve current readiness behavior and compatibility data.",
    progressLabel: "Readiness Score",
    starInstructionHook: "preparedness_participation_instruction",
  },
  { key: "community-projects", title: "Community Projects", description: "Organize projects, teams, milestones, and member contribution pathways.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.service, icon: "📌", memberCta: "Coming Soon" },
  { key: "mutual-aid", title: "Mutual Aid", description: "Coordinate trusted support requests, delivery help, and resource verification.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.service, icon: "🫱🏾‍🫲🏿", memberCta: "Coming Soon" },
  { key: "volunteer-center", title: "Volunteer Center", description: "Find and coordinate service roles when volunteer workflows are activated.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.service, icon: "🙋🏾", memberCta: "Coming Soon" },
  { key: "community-gardens", title: "Community Gardens", description: "Reserve space for gardens, plots, seasonal progress, tools, seeds, and volunteers.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.food, icon: "🌱", memberCta: "Coming Soon" },
  { key: "food-distribution", title: "Food Distribution", description: "Coordinate meals, pantry boxes, drivers, pickup points, and location readiness.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.food, icon: "🥘", memberCta: "Coming Soon" },
  { key: "transportation-support", title: "Transportation Support", description: "Reserve future ride, delivery, and mobility support coordination.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.service, icon: "🚐", memberCta: "Coming Soon" },
  { key: "elder-care", title: "Elder Care", description: "Coordinate check-ins, practical care, and trusted support for elders.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.service, icon: "👵🏾", memberCta: "Coming Soon" },
  { key: "emergency-response", title: "Emergency Response", description: "Reserve future response teams, communications, status tracking, and needs triage.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.readiness, icon: "🚨", memberCta: "Coming Soon" },
  { key: "community-chapters", title: "Community Chapters", description: "Activate local chapters, neighborhood circles, and regional operations.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.chapters, icon: "📍", memberCta: "Coming Soon" },
  { key: "community-funding", title: "Community Funding", description: "Move resources toward projects, mutual support, and cooperative development.", route: null, status: OPERATION_MODULE_STATUSES.comingSoon, category: OPERATION_MODULE_CATEGORIES.economy, icon: "💰", memberCta: "Coming Soon" },
];

export function getOperationModule(key) {
  return COMMUNITY_OPERATION_MODULES.find((module) => module.key === key);
}

export function mapPreparednessActivityToOperation(activity) {
  return {
    moduleKey: "preparedness",
    activityType: activity.activityType || activity.activity_type || "preparedness_update",
    actor: activity.actor || activity.member || "Community member",
    text: activity.text || activity.message || "Preparedness activity recorded.",
    createdAt: activity.createdAt || activity.created_at || new Date().toISOString(),
    visibility: activity.visibility || "community",
    metadata: activity.metadata || {},
  };
}
