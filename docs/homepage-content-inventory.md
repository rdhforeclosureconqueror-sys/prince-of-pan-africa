# Homepage Learning Content Inventory

This inventory records the repository content found before adding or rewriting homepage learning content for the member launchpad/dashboard redesign.

## Swahili vocabulary content

- `public/languages/swahili_30days.json` contains a 30-day Swahili micro-lesson dataset with daily themes, vocabulary words, example sentences, pronunciation hints, tips, and culture notes.
- `public/languages/swahili.html` renders the Swahili lesson-of-the-day experience and match-game flow using the Swahili dataset.
- `public/languages/matchGame.js` and `public/languages/lessonTts.js` provide shared public-language lesson interactions and audio support.

## Historical fact content

- `src/data/blackHistoryFacts.js` contains monthly Black history highlight arrays and a `getMonthlyHighlights(monthName)` helper.
- `src/data/timelineEvents.js` contains a concise Africa origins timeline with summaries and detail copy.
- `src/data/timelineA_africaOrigins.js` contains a sourced Africa origins timeline with date labels, regions, tags, summaries, and source links.

## Forgotten Black Mega Cities content

- `docs/community-binder/website-foundation-v1.md` includes a foundational-text section for `Forgotten Black Mega Cities`, including purpose, core lessons, and its relationship to Simba wa Ujamaa.
- No dedicated structured JavaScript/JSON dataset for Forgotten Black Mega Cities was found in `src/data` or `public/languages`.

## African history content

- `src/data/timelineA_africaOrigins.js` provides structured African origins entries spanning Jebel Irhoud, Nabta Playa, predynastic Nile Valley cultures, Early Dynastic Egypt, and Old Kingdom Egypt.
- `src/data/timelineEvents.js` provides a smaller Africa origins timeline for UI usage.
- `src/data/portals/decolo30.js` includes decolonization study material with African, Afro-Indigenous, ancestral-study, economy, and historical-method framing across a 30-day portal curriculum.

## Blackonomics content

- `docs/community-binder/website-foundation-v1.md` includes a foundational-text section for `Blackonomics`, including purpose, core lessons, and its relationship to Simba wa Ujamaa.
- No dedicated structured JavaScript/JSON Blackonomics dataset was found in `src/data` or `public/languages`.

## Existing educational datasets

- `public/languages/swahili_30days.json` and `public/languages/yoruba_30days.json` provide language-learning datasets.
- `src/data/leadershipQuestions.js` provides leadership assessment content.
- `src/data/blackHistoryFacts.js`, `src/data/timelineEvents.js`, and `src/data/timelineA_africaOrigins.js` provide historical learning content.
- `src/data/portals/decolo30.js` provides a 30-day decolonization learning portal curriculum.
