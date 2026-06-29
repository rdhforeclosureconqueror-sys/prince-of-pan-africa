import React from "react";
import { Link } from "react-router-dom";
import "../styles/applications.css";

function ActionLink({ label, path, variant = "primary" }) {
  if (!label || !path) return null;
  return <Link className={`application-card__button application-card__button--${variant}`} to={path}>{label}</Link>;
}

function ApplicationActions({ application }) {
  if (application.current) {
    return <span className="application-card__button application-card__button--disabled">You are here</span>;
  }

  if (application.primary_cta_path || application.secondary_cta_path) {
    return (
      <div className="application-card__actions">
        <ActionLink label={application.primary_cta_label || application.launchLabel || "Learn More"} path={application.primary_cta_path || application.route} />
        <ActionLink label={application.secondary_cta_label} path={application.secondary_cta_path} variant="secondary" />
      </div>
    );
  }

  if (application.route) {
    return <Link className="application-card__button" to={application.route}>{application.launchLabel || "Launch"}</Link>;
  }

  if (application.externalUrl && application.status !== "Invite Only") {
    return <a className="application-card__button" href={application.externalUrl} target="_blank" rel="noreferrer">{application.launchLabel || "Launch"}</a>;
  }

  return <button className="application-card__button application-card__button--disabled" type="button" disabled>{application.status}</button>;
}

export default function ApplicationCard({ application, compact = false }) {
  const isExternal = application.status === "External Platform" || application.status === "Invite Only";
  const statusClass = application.status.toLowerCase().replace(/\s+/g, "-");

  return (
    <article className={`application-card ${compact ? "application-card--compact" : ""} ${isExternal ? "application-card--external" : ""} ${application.society_builder_related ? "application-card--society" : ""}`}>
      <div className="application-card__topline">
        <span className="application-card__icon" aria-hidden="true">{application.icon}</span>
        <span className={`application-card__status application-card__status--${statusClass}`}>{application.status}</span>
      </div>
      <div className="application-card__body">
        <p className="application-card__category">{application.platformPurpose || application.category}</p>
        <h3>{application.name}</h3>
        <p>{application.description}</p>
        {!compact ? <strong>{application.purpose}</strong> : null}
        {!compact && application.status_message ? <p className="application-card__status-message">{application.status_message}</p> : null}
        {!compact && application.recommended_first_focus ? (
          <p className="application-card__metadata">
            <span>First focus:</span> {application.recommended_first_focus}
          </p>
        ) : null}
      </div>
      <ApplicationActions application={application} />
    </article>
  );
}
