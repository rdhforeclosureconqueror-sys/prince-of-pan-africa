# Membership Role Migration Plan

Status: Prepared before Stripe or Discord implementation.

## Approved Launch Roles

The launch membership role model is:

- `community_member`
- `builder_member`
- `admin`
- `superadmin`

## Legacy Role Mapping

Existing repository roles map into the launch model as follows:

| Legacy role | Launch role | Rationale |
| --- | --- | --- |
| `member` | `community_member` | Existing basic member accounts align with the Community Member path. |
| `subscriber` | `builder_member` | Existing subscriber accounts had elevated organizer access and are the closest match to Builder-level participation. |
| `admin` | `admin` | Administrative role remains unchanged. |
| `superadmin` | `superadmin` | Superadmin role remains unchanged. |

## Application Compatibility

The RBAC normalizer maps legacy `member` and `subscriber` role values to the launch roles at runtime. This allows existing users to keep signing in while database rows are migrated.

## Database Migration Steps

Run after launch roles have been seeded in the target environment:

1. Back up the production database.
2. Verify the roles table contains `community_member`, `builder_member`, `admin`, and `superadmin`.
3. Update legacy `users.role` values:
   - `member` → `community_member`
   - `subscriber` → `builder_member`
4. Update legacy `member_profiles.role` values using the same mapping.
5. For any existing `user_roles` rows pointing to legacy `member` or `subscriber` roles:
   - Add the equivalent launch role if it is not already attached.
   - Remove the legacy role attachment after verification.
6. Leave legacy role rows in place temporarily for rollback safety.
7. After a full release cycle with no legacy role references, archive or delete legacy role rows.

## Post-Migration Verification

Verify:

- Existing `member` users resolve as `community_member`.
- Existing `subscriber` users resolve as `builder_member`.
- `community_member` users receive community permissions and dashboard access.
- `builder_member` users receive community permissions plus Builder permissions and organizer access.
- Admin and superadmin users retain operations access.

## Out of Scope for This Phase

Stripe and Discord are intentionally not implemented in this migration phase. Stripe will become the source of truth for paid membership state in a later phase, and Discord role sync will be planned after Stripe planning is complete.
