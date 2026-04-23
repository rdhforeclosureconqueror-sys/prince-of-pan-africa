# Brain Training Milestone 1 — Live/Manual Runtime Verification

**Date:** 2026-04-23 (UTC)  
**Repo:** `/workspace/prince-of-pan-africa`  
**Requested scope:** Live/manual verification of Song Keys, Sight Memory, and Brain Training UI/UX.

## Execution status

I attempted to perform true live/manual runtime verification against a running app, but browser runtime tooling is unavailable in this environment:

- Frontend build succeeds.
- Browser automation package access is blocked by registry policy (`403 Forbidden` for Playwright).

Because of that, this report includes:
1) what I **explicitly attempted live**, and  
2) code-level verification of gameplay/UI logic paths that are relevant to the requested checks.

## Exact checks performed

1. Ran production build to verify current frontend compiles:
   - `npm run build`
2. Attempted to use browser runtime tooling for live/manual execution:
   - `npx playwright --version`
3. Reviewed implementation for Song Keys runtime logic:
   - `src/games/rhythmGame.js`
4. Reviewed implementation for Sight Memory runtime logic:
   - `src/games/sightGame.js`
5. Reviewed Brain Training shell/tabs/stat sync layout wiring:
   - `src/pages/BrainTraining.jsx`
6. Reviewed Brain Training and game styling for desktop/mobile/dark-blue fidelity:
   - `src/styles/brainTraining.css`

## Expected vs actual

## 1) Song Keys

### falling notes render correctly
- **Expected:** Notes fall in lanes and align to hit zone timing.
- **Actual:** Implemented as animated `.falling-note` elements per unresolved note with top position derived from timing progress; notes are removed/re-rendered per frame.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### hit line is clear
- **Expected:** Hit line is visually obvious.
- **Actual:** Dedicated `lane-board__hit-line` element is always rendered in board layout.
- **Status:** **PARTIALLY VERIFIED (markup/styling path)** / **LIVE UNVERIFIED**.

### A/S/D/F/G input works
- **Expected:** Keyboard input for A,S,D,F,G maps to 5 lanes.
- **Actual:** `keydown` listener maps uppercased key to `LANE_KEYS = ["A","S","D","F","G"]` and dispatches lane press handling.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### timing judgments (Perfect/Good/OK/Miss) trigger correctly
- **Expected:** Four judgment outcomes based on timing windows.
- **Actual:** `getJudgement` returns `Perfect`, `Good`, `OK` by proportional hit-window thresholds; out-of-window resolves to `Miss` via no-judgement path.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### combo/score/accuracy update correctly
- **Expected:** Stats reflect hit/miss outcomes in real time.
- **Actual:** Hits increment `score`, `hits`, `combo`; misses reset combo and increment attempts; accuracy computed as `hits/attempts`; UI stat nodes updated via `updateStats()`.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### tempo and difficulty selectors affect gameplay correctly
- **Expected:** Selector changes impact beat spacing and hit/fall behavior.
- **Actual:** Difficulty changes alter `fallMs`, `hitWindowMs`, `densityMultiplier`; tempo alters BPM input into timeline generation.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### built-in patterns feel playable and musical
- **Expected:** Patterns feel musical and ergonomic.
- **Actual:** Multiple fixed patterns exist (public-domain and original), but subjective playability cannot be validated without live play.
- **Status:** **LIVE UNVERIFIED**.

## 2) Sight Memory

### exactly one card is shown
- **Expected:** One card appears during reveal.
- **Actual:** Stage is replaced with a single `memory-card` article during reveal (`stage.replaceChildren(cardNode)`), then hidden placeholder.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### reveal timer hides the card at the correct time
- **Expected:** Card hides exactly at selected reveal duration.
- **Actual:** `setTimeout(..., revealSeconds * 1000)` triggers question phase; timer can be invalidated and cleared.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### recall questions are generated only from shown features
- **Expected:** Questions reference only displayed attributes.
- **Actual:** Question generation uses `code`, `color`, `symbol`, plus `borderStyle`/`accentMark` only when present on shown card.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### easy mode uses exactly 3 digits + 1 color + 1 symbol
- **Expected:** Easy card includes 3-digit code and only one color + one symbol attribute.
- **Actual:** Easy `buildCard()` returns 3-digit number string (`100-999`) with color + symbol only.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### reset clears round cleanly
- **Expected:** Reset clears timers, card, questions, stats progression.
- **Actual:** Reset invalidates round id, clears timer, resets level/score/attempts, nulls active card, resets stage/question panel/feedback.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

### no stuck overlay/timer bug occurs
- **Expected:** No stale timer or ghost round after reset/start changes.
- **Actual:** Round invalidation + timeout clearing guards exist and should prevent stale callback actions.
- **Status:** **PARTIALLY VERIFIED (logic)** / **LIVE UNVERIFIED**.

## 3) UI/UX

### desktop layout feels correct
- **Expected:** Balanced two-column desktop dashboard.
- **Actual:** Grid/sidebar/main structure and section cards are implemented; subjective spacing/readability requires live render.
- **Status:** **PARTIALLY VERIFIED (structure)** / **LIVE UNVERIFIED**.

### mobile layout is usable
- **Expected:** Responsive single-column flow remains usable.
- **Actual:** Responsive rules exist for key breakpoints and stack behavior; real-device usability not runnable here.
- **Status:** **PARTIALLY VERIFIED (CSS rules)** / **LIVE UNVERIFIED**.

### dark-blue dashboard styling is consistent
- **Expected:** Consistent dark-blue themed visual language.
- **Actual:** Theme classes/colors are consistently defined in Brain Training stylesheet and game skins.
- **Status:** **PARTIALLY VERIFIED (style definitions)** / **LIVE UNVERIFIED**.

### Brain Training now feels aligned with intended product
- **Expected:** Overall interaction and visual tone matches product direction.
- **Actual:** Structural and logic alignment appears strong at code level; experiential alignment cannot be validated without actual manual runtime session.
- **Status:** **LIVE UNVERIFIED**.

## Remaining gameplay issues

1. **Live playability and timing feel remain unvalidated** due to inability to run manual/browser checks.
2. **Pattern musicality/ergonomics remain unvalidated** (subjective and requires human play session).
3. **Judgment feel calibration remains unvalidated** at runtime (especially edge timing and key repeat behavior).

## Remaining layout issues

1. **No definitive visual defects confirmed** (live rendering unavailable).
2. **Desktop and mobile UX fit/spacing still need hands-on verification** in real browser viewports.

## PASS / FAIL

**FAIL** — Required live/manual runtime verification could not be completed in this environment because browser runtime tooling is unavailable (`playwright` install blocked by registry policy).

## Command evidence

- `npm run build` → PASS
- `npx playwright --version` → FAIL (`E403 Forbidden` package access policy)
