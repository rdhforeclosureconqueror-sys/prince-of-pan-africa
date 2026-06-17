# Phase 6 — Community Labor Exchange

The Community Labor Exchange turns Simba wa Ujamaa participation into a cooperative trust system. STAR Community Credits remain the measurement layer, but the product is not a point system: the product is members helping, verifying, and strengthening one another.

## Labor Categories

Every contribution should map to one of four labor categories:

1. **Learning Labor** — self-improvement through lessons, chapters, audiobooks, brain games, and Decolonization study.
2. **Community Labor** — helping members through welcomes, answers, moderation, events, and verification.
3. **Growth Labor** — growing Simba through shares, invitations, videos, testimonials, book recommendations, and partners.
4. **Builder Labor** — improving the platform through bugs, feature tests, lessons, translations, educational uploads, and documentation.

## MVP Verification Flow

1. A member submits a contribution with proof, such as a screenshot link from a Discord verification thread.
2. The contribution is recorded as a pending Participation Engine activity.
3. Three different members verify the contribution.
4. Verifier #1 receives +3 STAR for verification labor.
5. Verifier #2 receives +1 STAR.
6. Verifier #3 receives +1 STAR.
7. Once the third confirmation is recorded, the original contribution becomes verified and the original member receives STAR.
8. Community Reputation updates separately from STAR for both the contributor and verifiers.

## Current Backend MVP

The backend now supports the platform-side verification primitive that a Discord bot or future website UI can call:

- `POST /participation/verification-requests` creates a pending labor contribution.
- `POST /participation/verification-requests/{activity_id}/verify` records member verification and completes the contribution after three confirmations.
- `GET /participation/reputation` returns the authenticated member's Community Reputation.

The Discord bot is intentionally not implemented here. The endpoint payload stores Discord workflow metadata so a bot can create/close verification threads without creating a separate tracking system.

## Trust Model

Community Reputation is separate from STAR. STAR measures awarded contribution credit. Reputation measures trustworthiness and service.

Tracked reputation fields include:

- Verified Contributions
- Verifications Completed
- Verification Accuracy
- Trust Score
- Leadership Level
- Consistency Streak

This creates the foundation for future cooperative systems such as community service verification, volunteer verification, local business participation, skill exchanges, mutual aid requests, barter exchanges, and cooperative ownership qualification.
