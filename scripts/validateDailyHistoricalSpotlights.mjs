import { DAILY_HISTORICAL_SPOTLIGHTS } from "../src/data/dailyHistoricalSpotlights.js";

const REQUIRED_FIELDS = [
  "date",
  "title",
  "did_you_know",
  "historical_context",
  "key_people_or_places",
  "why_it_matters_today",
  "reflection_question",
  "category",
  "source_note",
];

const START = "2026-06-15";
const END = "2026-12-31";
const EXPECTED_COUNT = 200;

const toDateKey = (date) => date.toISOString().slice(0, 10);
const addDays = (date, days) => {
  const next = new Date(date);
  next.setUTCDate(next.getUTCDate() + days);
  return next;
};

const expectedDateKeys = [];
for (let cursor = new Date(`${START}T00:00:00Z`); toDateKey(cursor) <= END; cursor = addDays(cursor, 1)) {
  expectedDateKeys.push(toDateKey(cursor));
}

const errors = [];

if (DAILY_HISTORICAL_SPOTLIGHTS.length !== EXPECTED_COUNT) {
  errors.push(`Expected ${EXPECTED_COUNT} records, found ${DAILY_HISTORICAL_SPOTLIGHTS.length}.`);
}

if (expectedDateKeys.length !== EXPECTED_COUNT) {
  errors.push(`Validation setup error: ${START} through ${END} should produce ${EXPECTED_COUNT} dates, found ${expectedDateKeys.length}.`);
}

const seenDates = new Set();
const actualDates = new Set();

DAILY_HISTORICAL_SPOTLIGHTS.forEach((entry, index) => {
  const label = `Record ${index + 1}${entry?.date ? ` (${entry.date})` : ""}`;

  REQUIRED_FIELDS.forEach((field) => {
    if (!Object.prototype.hasOwnProperty.call(entry, field) || String(entry[field]).trim() === "") {
      errors.push(`${label} is missing required field: ${field}.`);
    }
  });

  if (!/^2026-(06-(1[5-9]|2\d|30)|0[789]-\d{2}|1[012]-\d{2})$/.test(entry.date)) {
    errors.push(`${label} has an invalid date format or outside-range month/day: ${entry.date}.`);
  }

  if (entry.date < START || entry.date > END) {
    errors.push(`${label} date is outside ${START} through ${END}.`);
  }

  if (seenDates.has(entry.date)) {
    errors.push(`${label} duplicates date ${entry.date}.`);
  }
  seenDates.add(entry.date);
  actualDates.add(entry.date);

  const isOnThisDayTitle = entry.title.startsWith("On this day:");
  const isDailySpotlightTitle = entry.title.startsWith("Daily Spotlight:");
  const isExactSource = entry.source_note.startsWith("On this day; exact-date record");
  const isContextSource = entry.source_note.startsWith("Daily Spotlight; contextual record");

  if (!isOnThisDayTitle && !isDailySpotlightTitle) {
    errors.push(`${label} title must start with "On this day:" or "Daily Spotlight:".`);
  }

  if (isOnThisDayTitle && !isExactSource) {
    errors.push(`${label} uses "On this day" title but source_note is not marked as an exact-date record.`);
  }

  if (isDailySpotlightTitle && !isContextSource) {
    errors.push(`${label} uses "Daily Spotlight" title but source_note is not marked as a contextual record.`);
  }

  if (!isOnThisDayTitle && /\bOn this day\b/i.test(`${entry.did_you_know} ${entry.historical_context} ${entry.source_note}`)) {
    errors.push(`${label} is contextual but contains an "On this day" claim outside the title.`);
  }
});

expectedDateKeys.forEach((dateKey) => {
  if (!actualDates.has(dateKey)) {
    errors.push(`Missing date ${dateKey}.`);
  }
});

if (errors.length) {
  console.error("Daily Historical Spotlight dataset validation failed:");
  errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

console.log(`Daily Historical Spotlight dataset validation passed: ${EXPECTED_COUNT} complete records covering ${START} through ${END} with no duplicates.`);
