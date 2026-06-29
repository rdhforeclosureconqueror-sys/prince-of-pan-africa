import { COMMUNITY_OPERATION_MODULES, OPERATION_MODULE_STATUSES } from "../operations/communityOperationsRegistry";

export const APPLICATION_STATUSES = {
  available: "Available",
  comingSoon: "Coming Soon",
  external: "External Platform",
  inviteOnly: "Invite Only",
  organize: "Organize",
};

const SOCIETY_STATUS_MESSAGE = "This area becomes active when members organize a society or project around it.";

const SOCIETY_APPLICATION_OVERRIDES = {
  "community-projects": {
    description: "Create projects through your society instead of waiting for a separate project app.",
    purpose: "Organize shared work through Society Builder.",
    primary_cta_label: "Start a Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View My Societies",
    secondary_cta_path: "/societies",
    recommended_first_focus: "Community project",
  },
  "mutual-aid": {
    description: "Form mutual aid societies and care containers before launching support workflows.",
    purpose: "Build trusted care infrastructure through society formation.",
    primary_cta_label: "View Society Builder",
    primary_cta_path: "/society-builder",
    secondary_cta_label: "Start a Society",
    secondary_cta_path: "/societies/start",
    recommended_society_type: "Mutual Aid",
    recommended_first_focus: "Community care",
  },
  "community-gardens": {
    description: "Organize through a Garden Society or society project.",
    purpose: "Start a garden society or organize a garden project inside your existing society.",
    primary_cta_label: "Start a Garden Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View My Societies",
    secondary_cta_path: "/societies",
    recommended_society_type: "Neighborhood",
    recommended_first_focus: "Community garden",
  },
  "food-distribution": {
    description: "Organize through a food care team or mutual aid society.",
    purpose: "Coordinate food distribution through trusted society care teams.",
    primary_cta_label: "Start a Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View My Societies",
    secondary_cta_path: "/societies",
    recommended_society_type: "Mutual Aid",
    recommended_first_focus: "Food distribution",
  },
  "transportation-support": {
    description: "Organize through a transportation support circle.",
    purpose: "Build ride, delivery, and mobility support inside a society.",
    primary_cta_label: "Start a Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View My Societies",
    secondary_cta_path: "/societies",
    recommended_first_focus: "Transportation support",
  },
  "elder-care": {
    description: "Organize through elder care teams inside a society.",
    purpose: "Create elder care circles and trusted care teams.",
    primary_cta_label: "Start a Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View My Societies",
    secondary_cta_path: "/societies",
    recommended_first_focus: "Elder care",
  },
  "emergency-response": {
    description: "Organize through a preparedness society.",
    purpose: "Start an emergency response or preparedness society before the crisis.",
    primary_cta_label: "Start a Preparedness Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View Preparedness",
    secondary_cta_path: "/community/preparedness",
    recommended_society_type: "Preparedness",
    recommended_first_focus: "Emergency response",
  },
  "community-chapters": {
    description: "Register a chapter or build a local hub.",
    purpose: "Connect local chapters and neighborhood circles to Society Builder.",
    primary_cta_label: "Register a Chapter",
    primary_cta_path: "/societies/register-chapter",
    secondary_cta_label: "View Society Builder",
    secondary_cta_path: "/society-builder",
    recommended_society_type: "Chapter",
    recommended_first_focus: "Local hub",
  },
  "community-funding": {
    description: "Organize through a society with treasury rules and transparent reporting.",
    purpose: "Build funding circles only after trust, rules, and reporting are clear.",
    primary_cta_label: "Start a Society",
    primary_cta_path: "/societies/start",
    secondary_cta_label: "View Society Builder",
    secondary_cta_path: "/society-builder",
    recommended_first_focus: "Community funding circle",
  },
};

const reservedOperationApplications = COMMUNITY_OPERATION_MODULES
  .filter((module) => module.key !== "preparedness")
  .map((module) => {
    const override = SOCIETY_APPLICATION_OVERRIDES[module.key] || {};
    const societyRelated = module.key !== "volunteer-center";
    return {
      id: module.key,
      icon: module.icon,
      name: module.title,
      description: module.description,
      purpose: societyRelated ? "Start or join a society to build this area." : "Connect service roles to societies and projects as workflows open.",
      status: societyRelated ? APPLICATION_STATUSES.organize : module.status,
      category: societyRelated ? "Society Projects" : "Community Operations",
      launchLabel: module.memberCta,
      route: module.status === OPERATION_MODULE_STATUSES.available ? module.route : undefined,
      society_builder_related: societyRelated,
      society_focus_area: societyRelated,
      status_message: societyRelated ? SOCIETY_STATUS_MESSAGE : undefined,
      ...override,
    };
  });

export const SIMBA_APPLICATIONS = [
  { id: "member-home", icon: "🏠", name: "Member Home", description: "Your daily briefing, journey progress, recent wins, and next best step inside Simba.", purpose: "Know where you are and continue your growth journey.", status: APPLICATION_STATUSES.available, category: "Community", launchLabel: "Open Member Home", route: "/dashboard" },
  { id: "community", icon: "🤝", name: "Community", description: "Meet, verify, and collaborate with members across the Simba ecosystem.", purpose: "Meet and collaborate with members.", status: APPLICATION_STATUSES.available, category: "Community", launchLabel: "Open Community", route: "/community/directory" },
  { id: "library", icon: "📚", name: "Library", description: "Read, listen, and study Pan-African knowledge collections.", purpose: "Expand your knowledge.", status: APPLICATION_STATUSES.available, category: "Learning", launchLabel: "Open Library", route: "/library" },
  { id: "languages", icon: "🗣️", name: "Languages", description: "Practice African language pathways and reconnect through daily words and lessons.", purpose: "Reconnect with African languages.", status: APPLICATION_STATUSES.available, category: "Culture", launchLabel: "Open Languages", route: "/languages" },
  { id: "assessments", icon: "🧭", name: "Assessments", description: "Complete existing assessment journeys and review your saved growth reflections.", purpose: "Understand your current patterns.", status: APPLICATION_STATUSES.available, category: "Development", launchLabel: "Open Assessments", route: "/assessments" },
  { id: "learning", icon: "🎧", name: "Learning", description: "Continue study sessions, audiobooks, brain training, and guided learning moments.", purpose: "Keep learning with structured practice.", status: APPLICATION_STATUSES.available, category: "Learning", launchLabel: "Open Learning", route: "/study" },
  { id: "star-rewards", icon: "⭐", name: "STAR Rewards", description: "Track participation, milestones, and rewards earned through meaningful action.", purpose: "Recognize contribution and consistent participation.", status: APPLICATION_STATUSES.available, category: "Leadership", launchLabel: "View STAR", route: "/star-rewards" },
  { id: "preparedness", icon: "🛡️", name: "Community Preparedness", description: "Preparedness is mutual aid before the emergency. Start or join a preparedness society to build communication trees, supply plans, care teams, and emergency response capacity.", purpose: "Strengthen resilience through a preparedness society and current readiness resources.", status: APPLICATION_STATUSES.available, category: "Society Projects", launchLabel: "Open Preparedness", route: "/community/preparedness", society_builder_related: true, society_focus_area: true, recommended_society_type: "Preparedness", recommended_first_focus: "Community preparedness", primary_cta_label: "Start a Preparedness Society", primary_cta_path: "/societies/start", secondary_cta_label: "Open Preparedness", secondary_cta_path: "/community/preparedness" },
  { id: "characteristics", icon: "🌱", name: "Community Characteristics", description: "A future reflection layer for community strengths, needs, and development signals.", purpose: "Understand collective strengths without changing assessment scoring.", status: APPLICATION_STATUSES.comingSoon, category: "Development" },
  { id: "archetypes", icon: "🧬", name: "Community Archetypes", description: "Future community pattern language for coordination and support.", purpose: "Prepare shared language for future community development.", status: APPLICATION_STATUSES.comingSoon, category: "Development" },
  { id: "community-development", icon: "🏗️", name: "Community Development", description: "Build local capacity through societies, projects, and chapters.", purpose: "Turn community energy into structured development through Society Builder.", status: APPLICATION_STATUSES.organize, category: "Society Projects", society_builder_related: true, society_focus_area: true, recommended_first_focus: "Community development", primary_cta_label: "Start a Society", primary_cta_path: "/societies/start", secondary_cta_label: "Register a Chapter", secondary_cta_path: "/societies/register-chapter", status_message: SOCIETY_STATUS_MESSAGE },

  { id: "study-circles", icon: "⭕", name: "Study Circles", description: "Book-based learning groups organized by book, chapter, topic, reflection prompt, meeting, and member notes.", purpose: "Study together, discuss deeply, and let shared learning lead to future society formation.", status: APPLICATION_STATUSES.comingSoon, category: "Learning", primary_cta_label: "Open Learning", primary_cta_path: "/study", secondary_cta_label: "View Society Builder", secondary_cta_path: "/society-builder", status_message: "Study Circle remains a learning community area and can later connect groups into Society Builder." },
  { id: "mentorship", icon: "🦁", name: "Mentorship", description: "Connect learners, builders, elders, and guides through future mentorship pathways.", purpose: "Support growth through guided relationships.", status: APPLICATION_STATUSES.comingSoon, category: "Leadership" },
  { id: "cooperative-purchasing", icon: "🛒", name: "Cooperative Purchasing", description: "Cooperative purchasing becomes powerful when members organize a buying society, buying club, or institutional purchasing project.", purpose: "Build buying power through a society type, first focus, or future business integration.", status: APPLICATION_STATUSES.organize, category: "Society Projects", society_builder_related: true, society_focus_area: true, recommended_society_type: "Buying Society", recommended_first_focus: "Cooperative purchasing", primary_cta_label: "Start a Buying Society", primary_cta_path: "/societies/start", secondary_cta_label: "View My Societies", secondary_cta_path: "/societies", status_message: SOCIETY_STATUS_MESSAGE },
  ...reservedOperationApplications,
  { id: "garvey", icon: "🏪", name: "Garvey", platformPurpose: "Business Development Platform", description: "Business assessments, marketplace tools, landing pages, customer analytics, and growth engines remain in Garvey.", purpose: "Build and grow your business.", status: APPLICATION_STATUSES.external, category: "Economy", launchLabel: "Launch Garvey", externalUrl: "https://garvey.simbawu.com" },
  { id: "real-estate", icon: "🏘️", name: "Real Estate Platform", platformPurpose: "Investment Platform", description: "Independent community investment platform for property education, cooperative ownership, and wealth building.", purpose: "Build generational wealth.", status: APPLICATION_STATUSES.inviteOnly, category: "Future Systems" },
  { id: "pocketpt", icon: "💪🏾", name: "Pocket PT", platformPurpose: "Community Health Platform", description: "Independent health platform for fitness, nutrition, wellness, and physical readiness.", purpose: "Strengthen your body.", status: APPLICATION_STATUSES.comingSoon, category: "Health", launchLabel: "Notify Me" },
];

export const APPLICATION_CATEGORIES = ["Community", "Society Projects", "Community Operations", "Learning", "Development", "Economy", "Health", "Leadership", "Culture", "Future Systems"];

export function applicationsByCategory(applications = SIMBA_APPLICATIONS) {
  return APPLICATION_CATEGORIES.map((category) => ({
    category,
    applications: applications.filter((application) => application.category === category),
  })).filter((group) => group.applications.length > 0);
}
