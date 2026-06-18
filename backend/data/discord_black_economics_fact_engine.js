// Discord Black Economics Fact Engine
// Usage: const { getRandomFact, getFactById, facts } = require("./discord_black_economics_fact_engine");

const fs = require("fs");
const path = require("path");

const dataPath = path.join(__dirname, "black_economics_365_facts.json");
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const facts = data.facts;
const sources = data.sources;

function getRandomFact(options = {}) {
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

function getFactById(id) {
  return facts.find(f => f.id === Number(id)) || null;
}

function formatForDiscord(fact, includeSource = false) {
  if (!fact) return "No matching Black economics fact found.";
  let message = fact.discord_post;
  if (includeSource && sources[fact.source_key]) {
    message += `\n\n📚 Source: ${sources[fact.source_key].citation}`;
  }
  return message;
}

module.exports = { facts, sources, getRandomFact, getFactById, formatForDiscord };

// CLI test: node discord_black_economics_fact_engine.js
if (require.main === module) {
  console.log(formatForDiscord(getRandomFact(), false));
}
