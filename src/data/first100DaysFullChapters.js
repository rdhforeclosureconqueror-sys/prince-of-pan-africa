import { FIRST_100_DAYS_HANDBOOK_SOURCE } from "./containers/first100DaysHandbookSource.js";

export const FIRST_100_DAYS_FULL_SOURCE_TITLE = "Mutual Aid Society Handbook / First 100 Days Container";

const CHAPTER_HEADING = /^Chapter\s+(\d+):\s+(.+)$/gm;
const SECTION_HEADINGS = ["Core Question", "Understand", "Discuss", "Build", "Chapter Outputs", "Do in Simba"];

function splitSections(chapterText) {
  const lines = chapterText.split("\n");
  const sections = [];
  let active = null;

  for (const line of lines) {
    const trimmed = line.trim();
    const matchingHeading = SECTION_HEADINGS.find((heading) => trimmed === heading || trimmed.startsWith(`${heading}:`));
    if (matchingHeading) {
      active = { heading: trimmed, body: [] };
      sections.push(active);
      const sameLineText = trimmed.startsWith(`${matchingHeading}:`) ? trimmed.slice(matchingHeading.length + 1).trim() : "";
      if (sameLineText) active.body.push(sameLineText);
      continue;
    }
    if (!active) continue;
    if (trimmed) active.body.push(trimmed);
  }

  return sections.map((section) => ({ ...section, body: section.body.length ? section.body : [""] }));
}

function parseChapters(source) {
  const matches = [...source.matchAll(CHAPTER_HEADING)];
  return matches.map((match, index) => {
    const chapterNumber = Number(match[1]);
    const start = match.index;
    const end = matches[index + 1]?.index ?? source.length;
    const chapterText = source.slice(start, end).trim();
    const fullSections = splitSections(chapterText);
    return {
      id: `chapter-${chapterNumber}`,
      chapterNumber,
      chapter_label: `Chapter ${chapterNumber}`,
      chapter_title: match[2].trim(),
      source_title: FIRST_100_DAYS_FULL_SOURCE_TITLE,
      source_reference: FIRST_100_DAYS_FULL_SOURCE_TITLE,
      full_sections: fullSections,
      full_text_sections: fullSections,
      worksheets: fullSections.filter((section) => section.heading.startsWith("Build")),
      worksheets_or_tables: [],
      chapter_outputs: fullSections.find((section) => section.heading === "Chapter Outputs")?.body || [],
      do_in_simba: fullSections.find((section) => section.heading === "Do in Simba")?.body || [],
      sequence_order: chapterNumber,
      raw_text: chapterText,
    };
  });
}

export const first100DaysFullChapters = parseChapters(FIRST_100_DAYS_HANDBOOK_SOURCE);

export function first100ChapterIdFromLabel(label = "") {
  const normalized = String(label).trim().toLowerCase();
  const chapter = normalized.match(/chapter\s+(\d+)/);
  if (chapter) return `chapter-${chapter[1]}`;
  return normalized.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function findFirst100FullChapter(chapterIdOrLabel) {
  const id = first100ChapterIdFromLabel(chapterIdOrLabel);
  return first100DaysFullChapters.find((chapter) => chapter.id === id) || null;
}
