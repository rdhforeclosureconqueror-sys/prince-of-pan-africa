const envDiscordInviteUrl = import.meta.env?.VITE_SIMBA_DISCORD_INVITE_URL || import.meta.env?.VITE_DISCORD_INVITE_URL || "";

export const memberOnboardingSettings = {
  discordInviteUrl: envDiscordInviteUrl,
  recommendedFirstBook: {
    title: "The Foundation Of Black Excellence",
    href: "/library",
  },
  recommendedFirstAssessment: {
    title: "Leadership Archetype Assessment",
    href: "/assessments/center",
  },
  recommendedFirstLanguageLesson: {
    title: "Swahili Foundations: Day 1",
    href: "/languages/swahili.html",
  },
  stepsEnabled: {
    mission: true,
    memberHome: true,
    discord: true,
    library: true,
    language: true,
    assessment: true,
    brainTraining: true,
    starAction: true,
    reflection: true,
  },
};

export const firstSevenDaysPathway = [
  {
    day: 1,
    key: "mission",
    title: "Welcome & Mission",
    tasks: ["Read the Simba mission", "Visit Member Home", "Join Discord"],
    nextAction: "Read the mission and start your first week.",
    href: "/dashboard",
  },
  {
    day: 2,
    key: "library",
    title: "Library",
    tasks: ["Open the Library", "Preview one book or audiobook"],
    nextAction: "Preview your first book or audiobook.",
    href: memberOnboardingSettings.recommendedFirstBook.href,
  },
  {
    day: 3,
    key: "language",
    title: "Language",
    tasks: ["Complete one Swahili or Yoruba lesson"],
    nextAction: "Practice one language lesson.",
    href: memberOnboardingSettings.recommendedFirstLanguageLesson.href,
  },
  {
    day: 4,
    key: "assessment",
    title: "Assessment",
    tasks: ["Take one assessment through the Assessment Center"],
    nextAction: "Take one assessment when you are ready.",
    href: memberOnboardingSettings.recommendedFirstAssessment.href,
  },
  {
    day: 5,
    key: "brainTraining",
    title: "Brain Training",
    tasks: ["Complete one brain game"],
    nextAction: "Complete a brain game session.",
    href: "/brain-training",
  },
  {
    day: 6,
    key: "starAction",
    title: "Community Participation",
    tasks: ["Earn STAR through one approved action"],
    nextAction: "Choose one approved action that already earns STAR.",
    href: "/dashboard",
  },
  {
    day: 7,
    key: "reflection",
    title: "Reflection",
    tasks: ["Review Member Home", "See progress", "Choose next journey"],
    nextAction: "Review progress and choose your next journey.",
    href: "/dashboard",
  },
].filter((step) => memberOnboardingSettings.stepsEnabled[step.key]);
