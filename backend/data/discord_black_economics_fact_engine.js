// Discord Black Economics Fact Engine reference helper.
// Production backend posting is implemented in backend/app/services/discord_bridge.py.

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const factsPath = path.join(__dirname, "black_economics_365_facts.json");
const sourcesPath = path.join(__dirname, "black_economics_sources.json");
const data = JSON.parse(fs.readFileSync(factsPath, "utf8"));
export const sources = JSON.parse(fs.readFileSync(sourcesPath, "utf8"));
export const facts = data.facts;

export function validateDataset() {
  if (!Array.isArray(facts) || facts.length < 365) {
    throw new Error("Black Economics facts must include at least 365 daily posts.");
  }
  for (const fact of facts) {
    if (!fact || !fact.id || !fact.title || !fact.discord_post || !fact.source_key) {
      throw new Error("Black Economics fact is missing required production fields.");
    }
    if (!sources[fact.source_key]) {
      throw new Error(`Black Economics source metadata missing for ${fact.source_key}.`);
    }
  }
}

validateDataset();

export function getRandomFact(options = {}) {
  let pool = facts;
  if (options.theme) {
    const theme = options.theme.toLowerCase();
    pool = pool.filter(f => f.theme.toLowerCase().includes(theme));
  }
  if (options.region) {
    const region = options.region.toLowerCase();
    pool = pool.filter(f => f.region.toLowerCase().includes(region));
  }
  if (options.tag) {
    const tag = options.tag.toLowerCase();
    pool = pool.filter(f => (f.tags || []).map(t => t.toLowerCase()).includes(tag));
  }
  if (!pool.length) return null;
  return pool[Math.floor(Math.random() * pool.length)];
}

export function getFactById(id) {
  return facts.find(f => f.id === Number(id)) || null;
}

export function formatForDiscord(fact, includeSource = false) {
  if (!fact) return "No matching Black economics fact found.";
  let message = fact.discord_post;
  if (includeSource && sources[fact.source_key]) {
    message += `\n\n📚 Source: ${sources[fact.source_key].citation}`;
  }
  return message;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(formatForDiscord(getRandomFact(), false));
}
