export const APPLICATION_STATUSES = {
  available: "Available",
  comingSoon: "Coming Soon",
  external: "External Platform",
  inviteOnly: "Invite Only",
};

export const SIMBA_APPLICATIONS = [
  { id: "member-home", icon: "🏠", name: "Member Home", description: "Your daily briefing, journey progress, recent wins, and next best step inside Simba.", purpose: "Know where you are and continue your growth journey.", status: APPLICATION_STATUSES.available, category: "Community", launchLabel: "Open Member Home", route: "/dashboard" },
  { id: "community", icon: "🤝", name: "Community", description: "Meet, verify, and collaborate with members across the Simba ecosystem.", purpose: "Meet and collaborate with members.", status: APPLICATION_STATUSES.available, category: "Community", launchLabel: "Open Community", route: "/community/directory" },
  { id: "library", icon: "📚", name: "Library", description: "Read, listen, and study Pan-African knowledge collections.", purpose: "Expand your knowledge.", status: APPLICATION_STATUSES.available, category: "Learning", launchLabel: "Open Library", route: "/library" },
  { id: "languages", icon: "🗣️", name: "Languages", description: "Practice African language pathways and reconnect through daily words and lessons.", purpose: "Reconnect with African languages.", status: APPLICATION_STATUSES.available, category: "Culture", launchLabel: "Open Languages", route: "/languages" },
  { id: "assessments", icon: "🧭", name: "Assessments", description: "Complete existing assessment journeys and review your saved growth reflections.", purpose: "Understand your current patterns.", status: APPLICATION_STATUSES.available, category: "Development", launchLabel: "Open Assessments", route: "/assessments" },
  { id: "learning", icon: "🎧", name: "Learning", description: "Continue study sessions, audiobooks, brain training, and guided learning moments.", purpose: "Keep learning with structured practice.", status: APPLICATION_STATUSES.available, category: "Learning", launchLabel: "Open Learning", route: "/study" },
  { id: "star-rewards", icon: "⭐", name: "STAR Rewards", description: "Track participation, milestones, and rewards earned through meaningful action.", purpose: "Recognize contribution and consistent participation.", status: APPLICATION_STATUSES.available, category: "Leadership", launchLabel: "View STAR", route: "/dashboard#star-rewards" },
  { id: "preparedness", icon: "🛡️", name: "Community Preparedness", description: "Household readiness, shared inventory, volunteer coordination, and hopeful community resilience practice.", purpose: "Practice unity through household and community preparedness.", status: APPLICATION_STATUSES.available, category: "Preparedness", launchLabel: "Open Preparedness", route: "/preparedness" },
  { id: "characteristics", icon: "🌱", name: "Community Characteristics", description: "A future reflection layer for community strengths, needs, and development signals.", purpose: "Understand collective strengths without changing assessment scoring.", status: APPLICATION_STATUSES.comingSoon, category: "Development" },
  { id: "archetypes", icon: "🧬", name: "Community Archetypes", description: "Future community pattern language for coordination and support.", purpose: "Prepare shared language for future community development.", status: APPLICATION_STATUSES.comingSoon, category: "Development" },
  { id: "community-development", icon: "🏗️", name: "Community Development", description: "Plan and coordinate long-term growth work across local and digital community systems.", purpose: "Turn community energy into structured development.", status: APPLICATION_STATUSES.comingSoon, category: "Community" },
  { id: "community-projects", icon: "📌", name: "Community Projects", description: "Organize future projects, teams, milestones, and member contribution pathways.", purpose: "Coordinate member effort around concrete outcomes.", status: APPLICATION_STATUSES.comingSoon, category: "Community" },
  { id: "volunteer-center", icon: "🙋🏾", name: "Volunteer Center", description: "Find and coordinate service opportunities when volunteer workflows are activated.", purpose: "Make service visible and easier to coordinate.", status: APPLICATION_STATUSES.comingSoon, category: "Leadership" },
  { id: "local-chapters", icon: "📍", name: "Local Chapters", description: "Future local organizing spaces for regions, cities, and neighborhoods.", purpose: "Build local relationships beyond the screen.", status: APPLICATION_STATUSES.comingSoon, category: "Community" },
  { id: "study-circles", icon: "⭕", name: "Study Circles", description: "Small group learning circles for books, language, history, and practical development.", purpose: "Learn in community with accountability.", status: APPLICATION_STATUSES.comingSoon, category: "Learning" },
  { id: "mutual-aid", icon: "🫱🏾‍🫲🏿", name: "Mutual Aid", description: "Reserve space for future coordinated support, requests, and trusted contribution flows.", purpose: "Help members support one another responsibly.", status: APPLICATION_STATUSES.comingSoon, category: "Community" },
  { id: "mentorship", icon: "🦁", name: "Mentorship", description: "Connect learners, builders, elders, and guides through future mentorship pathways.", purpose: "Support growth through guided relationships.", status: APPLICATION_STATUSES.comingSoon, category: "Leadership" },
  { id: "cooperative-purchasing", icon: "🛒", name: "Cooperative Purchasing", description: "Future coordination for buying together and strengthening community economics.", purpose: "Increase collective economic power.", status: APPLICATION_STATUSES.comingSoon, category: "Economy" },
  { id: "community-funding", icon: "💰", name: "Community Funding", description: "Future funding pathways for projects, mutual support, and cooperative development.", purpose: "Move resources toward community priorities.", status: APPLICATION_STATUSES.comingSoon, category: "Economy" },
  { id: "garvey", icon: "🏪", name: "Garvey", platformPurpose: "Business Development Platform", description: "Business assessments, marketplace tools, landing pages, customer analytics, and growth engines remain in Garvey.", purpose: "Build and grow your business.", status: APPLICATION_STATUSES.external, category: "Economy", launchLabel: "Launch Garvey", externalUrl: "https://garvey.simbawu.com" },
  { id: "real-estate", icon: "🏘️", name: "Real Estate Platform", platformPurpose: "Investment Platform", description: "Independent community investment platform for property education, cooperative ownership, and wealth building.", purpose: "Build generational wealth.", status: APPLICATION_STATUSES.inviteOnly, category: "Future Systems" },
  { id: "pocketpt", icon: "💪🏾", name: "PocketPT", platformPurpose: "Community Health Platform", description: "Independent health platform for fitness, nutrition, wellness, and physical readiness.", purpose: "Strengthen your body.", status: APPLICATION_STATUSES.external, category: "Health", launchLabel: "Launch PocketPT", externalUrl: "https://pocketpt.app" },
];

export const APPLICATION_CATEGORIES = ["Community", "Learning", "Development", "Economy", "Health", "Leadership", "Preparedness", "Culture", "Future Systems"];

export function applicationsByCategory(applications = SIMBA_APPLICATIONS) {
  return APPLICATION_CATEGORIES.map((category) => ({
    category,
    applications: applications.filter((application) => application.category === category),
  })).filter((group) => group.applications.length > 0);
}
