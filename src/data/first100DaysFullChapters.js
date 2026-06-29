import { CONTAINER_GUIDE_SOURCE_TITLE, containerGuideEntries } from "./societyContainerGuide";

const supplementalEntries = [
  {
    id: "appendix-k",
    chapterNumber: "K",
    chapterLabel: "Appendix K",
    title: "Skills, Assets, and Institutional Profiles",
    coreQuestion: "What capacity already exists in the society?",
    meaning: "The society records member skills, available assets, contributions, needs privacy, and current projects before assuming scarcity or recruiting from confusion.",
    whyItMatters: "Mutual aid becomes stronger when care teams and projects can see real capacity without exposing private needs or overusing the same members.",
    discuss: ["Which skills are already present?", "What should remain private?", "Where are the first gaps?"],
    build: ["Create the Skills and Assets Map.", "Invite members to complete Institutional Profiles.", "Match capacity to current needs and first actions."],
    recordInSimba: ["Save member profile and capacity notes in the Institutional Profile and Skills and Assets tools."],
  },
  {
    id: "appendix-l",
    chapterNumber: "L",
    chapterLabel: "Appendix L",
    title: "First Action Tracker",
    coreQuestion: "What small action can prove the container works?",
    meaning: "The first action is small, real, measurable, and recordable. It tests roles, money rules, care, decisions, assignments, and reporting before the society scales.",
    whyItMatters: "A modest completed action builds more trust than a large promise. The tracker turns intention into evidence.",
    discuss: ["Who is served or supported first?", "What resources are required?", "What would count as complete?"],
    build: ["Choose the first action.", "Assign a lead and members.", "Set date, resources, money needed, privacy level, and success measure."],
    recordInSimba: ["Use the First Action Tracker to save the plan and assignments."],
  },
  {
    id: "appendix-n",
    chapterNumber: "N",
    chapterLabel: "Appendix N",
    title: "Founding Roles",
    coreQuestion: "Who carries each responsibility?",
    meaning: "Founding roles make responsibility visible: facilitator, treasurer, assistant treasurer, recordkeeper, care coordinator, and other support roles as capacity allows.",
    whyItMatters: "Named roles prevent invisible labor, protect money and records, and help members know where to bring questions.",
    discuss: ["Who is already doing the work?", "Which roles need two-person oversight?", "Which roles can rotate later?"],
    build: ["Assign founding roles.", "Name vacancies.", "Confirm what each role is responsible for during the first 100 days."],
    recordInSimba: ["Save role assignments in the First Ten, Directory, or Roles tools."],
  },
  {
    id: "week-11",
    chapterNumber: "11",
    chapterLabel: "Week 11",
    title: "Execute the First Action",
    coreQuestion: "Can the society complete what it planned?",
    meaning: "Week 11 moves the first action from preparation into completion while members protect privacy, roles, records, and the agreed success measure.",
    whyItMatters: "Execution reveals whether the container can coordinate care under real conditions.",
    discuss: ["What must happen before the action starts?", "Who confirms completion?", "What needs to be recorded immediately?"],
    build: ["Complete the action.", "Track participation, resources, and issues.", "Capture immediate results."],
    recordInSimba: ["Update the First Action Tracker with execution notes."],
  },
  {
    id: "week-12",
    chapterNumber: "12",
    chapterLabel: "Week 12",
    title: "Record First Action Results",
    coreQuestion: "What did the first action teach us?",
    meaning: "Week 12 turns the completed action into institutional memory by recording who was served or supported, money used, what worked, what broke, and what must change.",
    whyItMatters: "Without records, the society only has memory and opinion. With records, members can learn and improve.",
    discuss: ["What worked?", "What broke?", "What must change before the next action?"],
    build: ["Complete the after-action review.", "Record results and lessons.", "Carry changes into the Day 100 Report."],
    recordInSimba: ["Save first action results and lessons learned."],
  },
];

function sectionsFor(entry) {
  return [
    { heading: "Core teaching", body: [entry.meaning, entry.whyItMatters] },
    { heading: "Questions for study", list: entry.discuss },
    { heading: "Worksheet / build prompts", list: entry.build },
    { heading: "Record in Simba", list: entry.recordInSimba },
  ];
}

export const first100DaysFullChapters = [...containerGuideEntries, ...supplementalEntries].map((entry, index) => ({
  id: entry.id,
  chapter_label: entry.chapterLabel,
  chapter_title: entry.title,
  full_text_sections: sectionsFor(entry),
  worksheets_or_tables: entry.connectedTasks?.length ? [{ title: "Connected Trust Board tasks", rows: entry.connectedTasks }] : [],
  source_reference: CONTAINER_GUIDE_SOURCE_TITLE,
  sequence_order: index + 1,
}));

export function first100ChapterIdFromLabel(label = "") {
  const normalized = String(label).trim().toLowerCase();
  const chapter = normalized.match(/chapter\s+(\d+)/);
  if (chapter) return `chapter-${chapter[1]}`;
  const appendix = normalized.match(/appendix\s+([a-z])/i);
  if (appendix) return `appendix-${appendix[1].toLowerCase()}`;
  const week = normalized.match(/week\s+(\d+)/);
  if (week) return `week-${week[1]}`;
  return normalized.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function findFirst100FullChapter(chapterIdOrLabel) {
  const id = first100ChapterIdFromLabel(chapterIdOrLabel);
  return first100DaysFullChapters.find((chapter) => chapter.id === id) || null;
}
