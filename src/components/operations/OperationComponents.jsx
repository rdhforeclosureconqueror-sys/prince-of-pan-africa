import React from "react";
import { Link } from "react-router-dom";

export function OperationModuleHero({ module, children }) {
  return <header className="operation-hero"><p className="section-kicker">Community Operations</p><h1><span>{module.icon}</span> {module.title}</h1><p>{module.description}</p>{children}</header>;
}

export function OperationProgressPanel({ label, value, detail }) {
  return <article className="operation-panel operation-progress-panel"><span>{label}</span><strong>{value}%</strong><div className="community-progress"><span style={{ width: `${value}%` }} /></div><p>{detail}</p></article>;
}

export function OperationResourceCard({ resource }) {
  return <article className="operation-panel"><span>{resource.status}</span><h3>{resource.name}</h3><p>{resource.detail}</p><strong>{resource.level}</strong></article>;
}

export function OperationRoleCard({ role }) {
  return <article className="operation-panel"><span>{role.status}</span><h3>{role.title}</h3><p>{role.description}</p><strong>{role.member || "Volunteer needed"}</strong></article>;
}

export function OperationActivityFeed({ activities }) {
  return <section className="operation-panel operation-activity-feed"><p className="section-kicker">Operations Activity</p><h2>Latest Preparedness Activity</h2>{activities.map((activity) => <article key={`${activity.activityType}-${activity.createdAt}`}><span>{activity.activityType.replaceAll("_", " ")}</span><strong>{activity.text}</strong><small>{activity.actor} · {new Date(activity.createdAt).toLocaleDateString()}</small></article>)}</section>;
}

export function ComingSoonOperationCard({ module }) {
  return <article className="operation-panel operation-coming-soon"><span>{module.icon}</span><h3>{module.title}</h3><p>{module.description}</p><button type="button" disabled>{module.memberCta}</button></article>;
}

export function OperationActionLink({ to, children }) {
  return <Link to={to} className="member-action-btn">{children}</Link>;
}
