# Daily Historical Spotlight Enrichment Plan

## Purpose

The Daily Historical Spotlight dataset is now structurally complete for June 15 through December 31, with 200 validated records. The next sprint should enrich the records gradually, not rewrite the full dataset at once. The goal is to reduce repeated entries, strengthen emotional and educational impact, and preserve the current validation guarantees while replacing generic contextual spotlights with better-sourced, more specific records.

## Current baseline

- Dataset coverage: June 15 through December 31, 2026.
- Current record count: 200 entries.
- Validation guardrail: every record must include `date`, `title`, `did_you_know`, `historical_context`, `key_people_or_places`, `why_it_matters_today`, `reflection_question`, `category`, and `source_note`.
- Current pattern: many contextual records repeat across the date range. The first enrichment pass should prioritize repeated titles before polishing already-specific exact-date entries.
- Exact-date entries already present should be preserved unless a stronger source or clearer wording is found: Juneteenth on June 19, Frederick Douglass on July 5, the March on Washington on August 28, Rosa Parks on December 1, the Montgomery Bus Boycott on December 5, and the Thirteenth Amendment on December 6.

## Priority dates that need stronger entries

### Sprint 1: Replace highest-repetition contextual records

These dates currently carry repeated contextual spotlights and should receive stronger, more specific entries first:

1. **June 15-June 18 and June 20-June 30**: the opening sequence establishes the product standard, so repeated Great Zimbabwe, Mali, Timbuktu, Aksum, Benin, Greenwood, Freedmen's Towns, HBCU, ironworking, and Swahili Coast entries should be diversified quickly.
2. **July 1-July 4 and July 6-July 31**: July should not feel like a loop after the July 5 Frederick Douglass anchor. Add more exact-date and specific contextual records tied to freedom, institution building, Black towns, African empires, science, and Pan-African politics.
3. **August 1-August 27 and August 29-August 31**: protect August 28 as a strong exact-date milestone, then build the surrounding month with entries on African women leaders, Black economic institutions, and Pan-African organizing.
4. **September 1-September 30**: use the month to add more African continent and diaspora balance, especially science, empires, cities, and political milestones outside the United States.
5. **October 1-October 31**: prioritize entries connected to Black political milestones, anti-colonial movements, community defense, and economic self-determination.
6. **November 1-November 30**: add deeper coverage of Black towns/cities, African women leaders, cultural institutions, and Pan-African movements.
7. **December 2-December 4 and December 7-December 31**: keep the existing December exact-date civil-rights anchors, then diversify the remaining dates so the end of the year closes with power, reflection, and momentum.

### Sprint 2: Strengthen exact-date density

For each month, identify at least five dates that can become exact-date records. Exact-date records should use `On this day:` only when the date is well-supported. If the date is uncertain, contested, commemorative, or thematic, keep `Daily Spotlight:` and explain that the record is contextual in `source_note`.

### Sprint 3: Improve repeated category language

After replacing high-repetition titles, review category names for consistency. Prefer stable category labels that support filtering and editorial analysis, such as `African empires`, `African science`, `Black towns/cities`, `Black economic institutions`, `Black political milestones`, `African women leaders`, and `Pan-African movements`.

## Category variety targets

Each enrichment batch should include a mix of the following categories instead of overusing one theme for long runs.

### African empires

Add specific entries that go beyond Mali, Aksum, Benin, and Great Zimbabwe. Candidate topics include Songhai, Ghana/Wagadu, Kongo, Oyo, Asante, Dahomey, Kanem-Bornu, Mutapa, Ndongo, Kush, and medieval Nubian kingdoms. Entries should show governance, trade, military organization, diplomacy, law, urbanism, and knowledge systems rather than only wealth or warfare.

### African science

Add records on astronomy, mathematics, medicine, metallurgy, agriculture, architecture, navigation, engineering, manuscript scholarship, environmental knowledge, and modern Black scientists. Balance ancient, medieval, and modern examples. Avoid vague claims; explain the specific knowledge practice and why it mattered.

### Black towns/cities

Expand beyond Greenwood and general freedmen's towns. Candidate topics include Nicodemus, Mound Bayou, Eatonville, Allensworth, Weeksville, Seneca Village, Africatown, Boley, Rosewood, Bronzeville, Harlem, Idlewild, Jackson Ward, Hayti in Durham, and Kinloch. Entries should identify the institutions that made each place powerful: land, schools, churches, newspapers, banks, businesses, cultural venues, and local government.

### Black economic institutions

Add specific banks, mutual-aid societies, insurance companies, newspapers, cooperatives, business districts, credit unions, farmer organizations, burial societies, professional networks, and buying clubs. Tie each entry to the practical question: how did Black communities pool capital, protect families, circulate dollars, and build durable institutions under exclusion?

### Black political milestones

Increase exact-date records tied to emancipation, Reconstruction, voting rights, civil rights, labor organizing, court cases, constitutional amendments, independence movements, local officeholding, and international diplomacy. Avoid making every political entry U.S.-centered; include Caribbean, African, Latin American, and global Black political history.

### African women leaders

Add entries for leaders, organizers, scholars, soldiers, diplomats, queens, market women, spiritual leaders, and institution builders. Candidate topics include Queen Nzinga, Yaa Asantewaa, Amina of Zazzau, Kandakes of Kush, Funmilayo Ransome-Kuti, Wangari Maathai, Ellen Johnson Sirleaf, Albertina Sisulu, Winnie Madikizela-Mandela, Amy Ashwood Garvey, Amy Jacques Garvey, and women in market associations and liberation movements.

### Pan-African movements

Add records on Pan-African congresses, Garveyism, the Universal Negro Improvement Association, anti-colonial conferences, Black internationalism, African liberation movements, diaspora solidarity campaigns, cultural festivals, student movements, and intellectual networks. Entries should connect people, places, institutions, and strategy across borders.

## Source and citation standard

Every enriched entry should meet this standard before it replaces an existing record:

1. **Minimum source count**: use at least two credible sources per enriched record when practical. At least one should be a primary, institutional, academic, museum, archive, government, or encyclopedia-quality source.
2. **Exact-date rule**: only use `On this day:` when the source clearly supports the month and day. If the event is known by year only, season only, a commemorative date, or a broad historical period, use `Daily Spotlight:`.
3. **Source note format**:
   - Exact-date: `On this day; exact-date record based on [brief source description].`
   - Contextual: `Daily Spotlight; contextual record based on [brief source description] rather than an exact-date claim.`
4. **No unsupported superlatives**: avoid claims like first, largest, richest, oldest, or only unless the source directly supports the wording.
5. **Respect complexity**: do not flatten people or communities into trauma-only narratives. Include agency, institution building, knowledge, strategy, and legacy.
6. **Citation tracking**: keep a working research note for each enriched batch with URLs, titles, publisher/author where available, access date, and the record date it supports. If source URLs are not added directly to the dataset, keep them in the sprint notes or future citation registry.
7. **Plagiarism guardrail**: write original summaries. Do not copy source wording except for short, attributed phrases when absolutely necessary.

## Review workflow before publishing enriched entries

1. **Select a small batch**: work in batches of 10 to 20 records, prioritizing the highest-repetition dates listed above.
2. **Research and draft**: create candidate replacements with source notes and research links before editing the dataset.
3. **Editorial review**: check each draft for accuracy, date confidence, category variety, tone, emotional strength, and age-appropriate clarity.
4. **Technical validation**: run `npm run validate:daily-spotlights` after edits to confirm date coverage, required fields, duplicate prevention, and title/source-note consistency.
5. **Repetition audit**: after each batch, summarize remaining repeated titles and categories so the next batch targets the biggest gaps.
6. **Product review**: inspect the member dashboard and calendar panel copy for readability if entries become longer or change tone significantly.
7. **Approval gate**: do not publish enriched entries until the batch has passed source review, editorial review, and validation.

## How to add future January 1-June 14 records later

The current dataset and validator intentionally cover June 15 through December 31. To add January 1 through June 14 later, use a separate expansion sprint rather than mixing it into enrichment work.

1. **Create the missing records**: add entries for January 1 through June 14 in chronological order before June 15.
2. **Update validator constants**: change the validator start date from `2026-06-15` to `2026-01-01` and increase the expected count from 200 to 365 for a non-leap-year 2026 dataset.
3. **Preserve date format**: continue using ISO date strings in the form `2026-MM-DD`.
4. **Keep exact-date discipline**: use `On this day:` only for well-sourced exact-date events; use `Daily Spotlight:` for contextual records.
5. **Balance the full-year calendar**: ensure January through June add variety instead of simply extending repeated cycles.
6. **Run validation**: run `npm run validate:daily-spotlights` after adjusting the dataset and validator.
7. **Document expansion sources**: keep source notes or a citation registry for the new records so future editors can audit exact-date claims.

## Definition of done for the enrichment-plan sprint

- The plan is committed before any broad rewrite of the 200 records.
- The current 200-record dataset remains unchanged during this planning step.
- The validator still passes against the existing June 15 through December 31 dataset.
- The next implementation sprint can pick a 10-to-20-record batch, source it, review it, and validate it without redesigning the workflow.
