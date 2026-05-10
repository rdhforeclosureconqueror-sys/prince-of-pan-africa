function normalizeList(values) {
  return Array.isArray(values) ? values.map((value) => String(value).toLowerCase()) : [];
}

export function isAdminUser(user, rbac) {
  if (!user) return false;

  const userRole = String(user?.role || "").toLowerCase();
  const roles = normalizeList(rbac?.roles);
  const permissions = normalizeList(rbac?.permissions);

  return (
    roles.includes("admin") ||
    roles.includes("superadmin") ||
    permissions.includes("admin:read_dashboard") ||
    userRole === "admin" ||
    userRole === "superadmin" ||
    user?.is_admin === true
  );
}

export function canAccessTextBookOrganizer(user, rbac, featureEnabled, authChecked) {
  const permissions = normalizeList(rbac?.permissions);

  return Boolean(
    featureEnabled &&
    authChecked &&
    user &&
    (isAdminUser(user, rbac) || permissions.includes("book_organizer:create_self")),
  );
}

export function canAccessMemberDashboard(user, rbac) {
  if (!user) return false;
  const permissions = normalizeList(rbac?.permissions);
  return isAdminUser(user, rbac) || permissions.includes("member:read_overview_self");
}

export function getDashboardLabel(user, rbac) {
  return isAdminUser(user, rbac) ? "Operations Deck" : "Member Dashboard";
}
