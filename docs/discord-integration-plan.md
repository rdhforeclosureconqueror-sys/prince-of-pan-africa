# Discord Integration Plan

Status: Planning only. Discord is not implemented in this phase.

## Role Model

Discord should mirror the launch membership model:

- Community Member Discord role
- Builder Member Discord role
- Admin/moderator roles as needed

## Required Environment Variables

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_COMMUNITY_ROLE_ID`
- `DISCORD_BUILDER_ROLE_ID`

If OAuth account linking is used:

- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`

## Backend Features To Build Later

- Discord account-linking endpoint.
- Discord callback endpoint if OAuth is used.
- Discord role-sync service.
- Admin retry endpoint for failed role sync attempts.
- Storage for Discord user ID and sync status.

## Dashboard Features To Build Later

- “Connect Discord” action.
- Discord connection status.
- Current assigned Discord role status.
- Instructions for accessing Community and Builder channels.

## Stripe-To-Discord Sync Later

After Stripe is implemented:

- Active Community subscription assigns the Community Discord role.
- Active Builder subscription assigns the Builder Discord role and any baseline Community access.
- Subscription cancellation or payment failure removes paid Discord roles after the final grace-period policy.

## Builder Channel Requirements

Builder Members should receive access to:

- Builder-focused discussions and channels.
- Testing-opportunity discussions.
- Feedback participation channels.
- Outreach and project-development discussions.

## Explicit Non-Goals For Current Phase

- No Discord bot installation.
- No OAuth flow.
- No Discord API calls.
- No automatic role assignment.
- No channel provisioning.
