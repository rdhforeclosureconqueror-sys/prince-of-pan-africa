import React from "react";
import { COMMUNITY_OPERATION_MODULES, getOperationModule, mapPreparednessActivityToOperation } from "../operations/communityOperationsRegistry";
import { ComingSoonOperationCard, OperationActivityFeed, OperationModuleHero, OperationProgressPanel, OperationResourceCard, OperationRoleCard } from "../components/operations/OperationComponents";
import "../styles/operations.css";

const preparednessResources = [
  { name: "Water", level: "3 days tracked", status: "Core resource", detail: "Store and rotate household water before crisis conditions begin." },
  { name: "Food", level: "Pantry check", status: "Core resource", detail: "Track shelf-stable meals, dietary needs, and gaps for your household." },
  { name: "Medical Supplies", level: "Needs review", status: "Shortage watch", detail: "Confirm first-aid basics, prescriptions, and health-specific supplies." },
  { name: "Power & Lighting", level: "Backup plan", status: "Resilience", detail: "Prepare charging, flashlights, batteries, and low-power communication routines." },
];

const preparednessRoles = [
  { title: "Water Manager", description: "Checks household water supply and rotation schedule.", status: "Preparedness role", member: "Assign locally" },
  { title: "Food Manager", description: "Reviews shelf-stable meals and nutrition needs.", status: "Preparedness role", member: "Assign locally" },
  { title: "Medical Coordinator", description: "Keeps medical supplies visible and current.", status: "Preparedness role", member: "Volunteer needed" },
  { title: "Power Manager", description: "Owns backup charging, light, and communication readiness.", status: "Preparedness role", member: "Volunteer needed" },
];

const preparednessActivity = [
  { activity_type: "readiness_check", actor: "Community member", message: "Reviewed household readiness and identified the next preparedness action.", created_at: "2026-06-20T00:00:00Z", metadata: { source: "compatibility_seed" } },
  { activity_type: "resource_review", actor: "Community member", message: "Checked water, food, medical, power, and lighting resources.", created_at: "2026-06-19T00:00:00Z", metadata: { source: "compatibility_seed" } },
].map(mapPreparednessActivityToOperation);

export default function CommunityPreparednessPage() {
  const module = getOperationModule("preparedness");
  const futureModules = COMMUNITY_OPERATION_MODULES.filter((item) => item.key !== "preparedness").slice(0, 4);

  return (
    <main className="operations-shell cosmic-readable-shell">
      <OperationModuleHero module={module}>
        <div className="operation-hero-actions"><a className="member-action-btn" href="#preparedness-command-center">Open Command Center</a><span className="trust-badge">First live operations module</span></div>
      </OperationModuleHero>

      <section id="preparedness-command-center" className="operation-command-layout">
        <OperationProgressPanel label={module.progressLabel} value={68} detail="Compatibility panel only: the reusable progress pattern wraps preparedness readiness without changing the scoring engine." />
        <article className="operation-panel"><p className="section-kicker">STAR Instructions</p><h2>Participation Hook</h2><p>Preparedness continues to use the existing STAR participation instruction system. This module exposes a hook name for future operation modules without changing STAR reward calculations.</p><strong>{module.starInstructionHook}</strong></article>
      </section>

      <section className="operation-section"><div><p className="section-kicker">Reusable Resource Pattern</p><h2>Preparedness Inventory</h2></div><div className="operation-grid">{preparednessResources.map((resource) => <OperationResourceCard key={resource.name} resource={resource} />)}</div></section>

      <section className="operation-section"><div><p className="section-kicker">Reusable Role Pattern</p><h2>Preparedness Volunteer Roles</h2></div><div className="operation-grid">{preparednessRoles.map((role) => <OperationRoleCard key={role.title} role={role} />)}</div></section>

      <OperationActivityFeed activities={preparednessActivity} />

      <section className="operation-section"><div><p className="section-kicker">Reserved Operations Modules</p><h2>Built to Grow Without Rewriting Preparedness</h2></div><div className="operation-grid">{futureModules.map((item) => <ComingSoonOperationCard key={item.key} module={item} />)}</div></section>
    </main>
  );
}
