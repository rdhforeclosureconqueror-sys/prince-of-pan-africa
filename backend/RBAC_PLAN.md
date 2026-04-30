# IAM-Style RBAC Authorization Plan (Design Only)

This document captures the proposed data-backed RBAC design and migration path for the current backend.

- Current state has role strings on `users`/`member_profiles` and cookie auth based on user id.
- No server-side permission checks are centralized.
- Several member/admin routes are currently unscoped or publicly callable.

See assistant response for full mapped plan and rollout order.
