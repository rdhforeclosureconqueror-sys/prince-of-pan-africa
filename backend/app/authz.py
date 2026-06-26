from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models import Permission, Role, User, UserRole

DEFAULT_ROLE_NAME = "community_member"
DEFAULT_ROLE_NAMES = ("community_member", "builder_member", "mutual_aid_reviewer", "mutual_aid_treasurer", "admin", "superadmin")
LEGACY_ROLE_ALIASES = {
    "member": "community_member",
    "subscriber": "builder_member",
}

DEFAULT_PERMISSION_NAMES = (
    "system:read_health",
    "system:read_verification",
    "system:run_dev_reset",
    "member:read_self",
    "member:update_self",
    "member:read_overview_self",
    "member:read_activity_self",
    "member:complete_community_onboarding",
    "membership:community",
    "membership:builder",
    "orientation:read_self",
    "updates:read_member",
    "library:read_member",
    "learning_paths:read_foundational",
    "dashboard:read_member",
    "discussion:access_community",
    "builder:access_channels",
    "builder:submit_feedback",
    "builder:join_testing",
    "builder:view_early_projects",
    "builder:track_contributions",
    "builder:participate_outreach",
    "assessment:submit_self",
    "assessment:read_self",
    "assessment:read_analytics",
    "audiobook:create_self",
    "audiobook:read_self",
    "audiobook:update_self",
    "audiobook:generate_audio_self",
    "audiobook:reflect_self",
    "book_organizer:create_self",
    "book_organizer:read_self",
    "book_organizer:update_self",
    "book_organizer:export_self",
    "chat:use",
    "voice:use_tts",
    "voice:use_stt",
    "admin:read_dashboard",
    "admin:read_users",
    "admin:manage_users",
    "admin:read_activity",
    "mutual_aid:create_request_self",
    "mutual_aid:read_request_self",
    "mutual_aid:read_requests_admin",
    "mutual_aid:review_requests",
    "mutual_aid:decide_requests",
    "mutual_aid:read_financial_controls",
    "mutual_aid:manage_disbursements",
)

BOOK_ORGANIZER_PERMISSION_NAMES = {
    "book_organizer:create_self",
    "book_organizer:read_self",
    "book_organizer:update_self",
    "book_organizer:export_self",
}

MEMBER_PERMISSION_NAMES = {
    "member:read_self",
    "member:update_self",
    "member:read_overview_self",
    "member:read_activity_self",
    "member:complete_community_onboarding",
    "membership:community",
    "orientation:read_self",
    "updates:read_member",
    "library:read_member",
    "learning_paths:read_foundational",
    "dashboard:read_member",
    "discussion:access_community",
    "assessment:submit_self",
    "assessment:read_self",
    "audiobook:create_self",
    "audiobook:read_self",
    "audiobook:update_self",
    "audiobook:generate_audio_self",
    "audiobook:reflect_self",
    "chat:use",
    "voice:use_tts",
    "voice:use_stt",
    "mutual_aid:create_request_self",
    "mutual_aid:read_request_self",
}

BUILDER_PERMISSION_NAMES = MEMBER_PERMISSION_NAMES | BOOK_ORGANIZER_PERMISSION_NAMES | {
    "membership:builder",
    "builder:access_channels",
    "builder:submit_feedback",
    "builder:join_testing",
    "builder:view_early_projects",
    "builder:track_contributions",
    "builder:participate_outreach",
}

ADMIN_EXTRA_PERMISSION_NAMES = {
    "admin:read_dashboard",
    "admin:read_users",
    "admin:manage_users",
    "admin:read_activity",
    "assessment:read_analytics",
    "mutual_aid:read_requests_admin",
    "mutual_aid:review_requests",
    "mutual_aid:decide_requests",
    "mutual_aid:read_financial_controls",
    "mutual_aid:manage_disbursements",
}


ROLE_PERMISSION_NAMES = {
    "community_member": MEMBER_PERMISSION_NAMES,
    "builder_member": BUILDER_PERMISSION_NAMES,
    "mutual_aid_reviewer": MEMBER_PERMISSION_NAMES | {"mutual_aid:review_requests"},
    "mutual_aid_treasurer": MEMBER_PERMISSION_NAMES | {"mutual_aid:read_financial_controls", "mutual_aid:manage_disbursements"},
    "admin": BUILDER_PERMISSION_NAMES | ADMIN_EXTRA_PERMISSION_NAMES,
    "superadmin": set(DEFAULT_PERMISSION_NAMES),
}


def normalize_role_name(role_name: str | None) -> str:
    normalized = (role_name or "").strip().lower()
    normalized = LEGACY_ROLE_ALIASES.get(normalized, normalized)
    return normalized if normalized in DEFAULT_ROLE_NAMES else DEFAULT_ROLE_NAME


def get_user_role_names(db: Session, user: User) -> list[str]:
    role_names = {
        name
        for (name,) in (
            db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
    }
    role_names.add(normalize_role_name(user.role))
    return sorted(role_names)


def get_user_permissions(db: Session, user: User) -> set[str]:
    role_names = get_user_role_names(db, user)
    permission_rows = (
        db.query(Permission.name)
        .join(Role.permissions)
        .filter(Role.name.in_(role_names))
        .all()
    )
    return {name for (name,) in permission_rows}


def user_has_permission(db: Session, user: User, permission_name: str) -> bool:
    return permission_name in get_user_permissions(db, user)


def _sync_user_roles(db: Session, user: User, roles_by_name: dict[str, Role]) -> None:
    normalized = normalize_role_name(user.role)
    role = roles_by_name[normalized]
    existing = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
        .first()
    )
    if not existing:
        db.add(UserRole(user_id=user.id, role_id=role.id))


def seed_rbac_defaults(db: Session) -> None:
    existing_roles = {role.name: role for role in db.query(Role).all()}
    for role_name in DEFAULT_ROLE_NAMES:
        if role_name not in existing_roles:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
            existing_roles[role_name] = role

    existing_permissions = {perm.name: perm for perm in db.query(Permission).all()}
    for permission_name in DEFAULT_PERMISSION_NAMES:
        if permission_name not in existing_permissions:
            permission = Permission(name=permission_name)
            db.add(permission)
            db.flush()
            existing_permissions[permission_name] = permission

    for role_name, permission_names in ROLE_PERMISSION_NAMES.items():
        role = existing_roles[role_name]
        attached = {permission.name for permission in role.permissions}
        for permission_name in permission_names:
            if permission_name not in attached:
                role.permissions.append(existing_permissions[permission_name])

    users: Iterable[User] = db.query(User).all()
    for user in users:
        _sync_user_roles(db, user, existing_roles)

    db.commit()
