import React, { useEffect, useMemo, useState } from "react";
import {
  getPreparednessSummary,
  logPreparednessInventory,
  savePreparednessProfile,
  savePreparednessVolunteer,
} from "../api/preparedness";
import {
  COMMUNITY_OPERATION_MODULES,
  getOperationModule,
  mapPreparednessActivityToOperation,
} from "../operations/communityOperationsRegistry";
import {
  ComingSoonOperationCard,
  OperationActivityFeed,
  OperationModuleHero,
  OperationProgressPanel,
  OperationResourceCard,
  OperationRoleCard,
} from "../components/operations/OperationComponents";
import "../styles/operations.css";
import "../styles/preparedness.css";

const emptyPreparedness = {
  preparedness_score: 0,
  community_readiness: "Building Together",
  household_participation: 0,
  volunteer_participation: 0,
  active_volunteers: 0,
  household_profiles: 0,
  inventory: [],
  critical_shortages: [],
  activity: [],
  profile: null,
  profile_score: 0,
};

const statusOptions = ["getting_started", "in_progress", "ready"];
const skillText = (value) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

function ProgressBar({ value }) {
  return (
    <span className="preparedness-progress">
      <span style={{ width: `${Math.min(100, value || 0)}%` }} />
    </span>
  );
}

function MetricCard({ label, value, detail }) {
  return (
    <article className="preparedness-card preparedness-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

export default function CommunityPreparednessPage() {
  const module = getOperationModule("preparedness");
  const futureModules = COMMUNITY_OPERATION_MODULES.filter(
    (item) => item.key !== "preparedness"
  ).slice(0, 4);

  const [data, setData] = useState(emptyPreparedness);
  const [roles, setRoles] = useState({});
  const [message, setMessage] = useState("");
  const [profile, setProfile] = useState({
    household_size: 1,
    neighborhood: "",
    water_days: 0,
    food_days: 0,
    medical_status: "getting_started",
    power_status: "getting_started",
    communication_status: "getting_started",
    skills: "",
    notes: "",
  });
  const [inventory, setInventory] = useState({
    item_name: "",
    category: "water",
    quantity: 1,
    unit: "units",
    target_quantity: 0,
    storage_location: "",
    notes: "",
  });
  const [volunteer, setVolunteer] = useState({
    role: "neighbor_support",
    availability: "as_available",
    neighborhood: "",
    skills: "",
    notes: "",
    active: true,
  });

  const loadSummary = () =>
    getPreparednessSummary()
      .then((res) => {
        const prepared = res.preparedness || emptyPreparedness;
        setData(prepared);
        setRoles(res.volunteer_roles || {});
        if (prepared.profile) {
          setProfile((current) => ({
            ...current,
            ...prepared.profile,
            skills: (prepared.profile.skills || []).join(", "),
          }));
        }
      })
      .catch(() =>
        setMessage(
          "Preparedness data is not available yet. The command center is ready for the backend when deployed."
        )
      );

  useEffect(() => {
    loadSummary();
  }, []);

  const radar = useMemo(
    () => [
      { label: "Preparedness", value: data.preparedness_score },
      {
        label: "Inventory",
        value: data.inventory.length
          ? Math.round(
              data.inventory.reduce((sum, item) => sum + item.percent, 0) /
                data.inventory.length
            )
          : 0,
      },
      { label: "Volunteers", value: data.volunteer_participation },
      { label: "Households", value: data.household_participation },
      {
        label: "Readiness",
        value: data.critical_shortages.length ? 45 : data.preparedness_score,
      },
    ],
    [data]
  );

  const operationActivity = useMemo(
    () =>
      (data.activity || []).map((item) =>
        mapPreparednessActivityToOperation({
          activity_type: item.type || item.activity_type || "preparedness",
          actor: item.actor || "Community member",
          message: item.title || item.text || item.message || "Preparedness activity recorded.",
          created_at: item.timestamp || item.created_at || item.createdAt,
          metadata: item.metadata || {},
        })
      ),
    [data.activity]
  );

  const submitProfile = (event) => {
    event.preventDefault();
    savePreparednessProfile({
      ...profile,
      household_size: Number(profile.household_size),
      water_days: Number(profile.water_days),
      food_days: Number(profile.food_days),
      skills: skillText(profile.skills),
    })
      .then((res) => {
        setData(res.preparedness);
        setMessage("Preparedness profile saved. One household strengthened the circle.");
      })
      .catch(() => setMessage("Sign in to save your household preparedness profile."));
  };

  const submitInventory = (event) => {
    event.preventDefault();
    logPreparednessInventory({
      ...inventory,
      quantity: Number(inventory.quantity),
      target_quantity: Number(inventory.target_quantity),
    })
      .then((res) => {
        setData(res.preparedness);
        setMessage("Supply logged. Shared resources make the community more capable.");
        setInventory((current) => ({ ...current, item_name: "", quantity: 1, notes: "" }));
      })
      .catch(() => setMessage("Sign in to log community supplies."));
  };

  const submitVolunteer = (event) => {
    event.preventDefault();
    savePreparednessVolunteer({ ...volunteer, skills: skillText(volunteer.skills) })
      .then((res) => {
        setData(res.preparedness);
        setMessage("Volunteer readiness saved. Cooperation grows through people who show up.");
      })
      .catch(() => setMessage("Sign in to register as a preparedness volunteer."));
  };

  return (
    <main className="preparedness-shell operations-shell cosmic-readable-shell">
      <OperationModuleHero module={module}>
        <div className="operation-hero-actions">
          <a className="member-action-btn" href="#preparedness-command-center">
            Open Command Center
          </a>
          <span className="trust-badge">First live operations module</span>
        </div>
      </OperationModuleHero>

      {message ? <div className="preparedness-notice">{message}</div> : null}

      <section id="preparedness-command-center" className="preparedness-command">
        <div className="preparedness-score-card">
          <p className="section-kicker">Command Center</p>
          <strong>{data.preparedness_score}</strong>
          <span>Preparedness Score</span>
          <p>{data.community_readiness}</p>
        </div>
        <MetricCard label="Households" value={data.household_profiles} detail={`${data.household_participation}% participation`} />
        <MetricCard label="Volunteers" value={data.active_volunteers} detail={`${data.volunteer_participation}% participation`} />
        <MetricCard label="Critical Shortages" value={data.critical_shortages.length} detail="Focus areas for shared action" />
      </section>

      <section className="operation-command-layout">
        <OperationProgressPanel
          label={module.progressLabel}
          value={data.preparedness_score}
          detail="Live preparedness readiness wrapped inside the reusable Community Operations progress pattern."
        />
        <article className="operation-panel">
          <p className="section-kicker">STAR Instructions</p>
          <h2>Participation Hook</h2>
          <p>
            Preparedness continues to use the existing STAR participation instruction system. This module exposes a hook name for future operation modules without changing STAR reward calculations.
          </p>
          <strong>{module.starInstructionHook}</strong>
        </article>
      </section>

      <section className="preparedness-grid-two">
        <article className="preparedness-card">
          <p className="section-kicker">Community Radar</p>
          <h2>Overall readiness</h2>
          {radar.map((item) => (
            <div className="preparedness-radar-row" key={item.label}>
              <span>{item.label}</span>
              <ProgressBar value={item.value} />
              <strong>{item.value}%</strong>
            </div>
          ))}
        </article>

        <article className="preparedness-card">
          <p className="section-kicker">Preparedness Profile</p>
          <h2>Your household path</h2>
          <p className="preparedness-profile-score">
            Current status: <strong>{data.profile_score || 0}% prepared</strong>
          </p>
          <ul className="preparedness-list">
            <li>Start with water and food for a few days, then build steadily.</li>
            <li>Add communication, power, and medical basics as your household is able.</li>
            <li>Share skills you can offer; no permanent labels, only growth.</li>
          </ul>
        </article>
      </section>

      <section className="preparedness-grid-two">
        <form className="preparedness-card preparedness-form" onSubmit={submitProfile}>
          <p className="section-kicker">Household Preparedness</p>
          <h2>Build your profile</h2>

          <label>
            Household size
            <input type="number" min="1" value={profile.household_size} onChange={(e) => setProfile({ ...profile, household_size: e.target.value })} />
          </label>

          <label>
            Neighborhood
            <input value={profile.neighborhood} onChange={(e) => setProfile({ ...profile, neighborhood: e.target.value })} />
          </label>

          <div className="preparedness-form-row">
            <label>
              Water days
              <input type="number" min="0" value={profile.water_days} onChange={(e) => setProfile({ ...profile, water_days: e.target.value })} />
            </label>
            <label>
              Food days
              <input type="number" min="0" value={profile.food_days} onChange={(e) => setProfile({ ...profile, food_days: e.target.value })} />
            </label>
          </div>

          {[["medical_status", "Medical"], ["power_status", "Power"], ["communication_status", "Communication"]].map(([key, label]) => (
            <label key={key}>
              {label}
              <select value={profile[key]} onChange={(e) => setProfile({ ...profile, [key]: e.target.value })}>
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>
          ))}

          <label>
            Skills
            <input placeholder="first aid, cooking, organizing" value={profile.skills} onChange={(e) => setProfile({ ...profile, skills: e.target.value })} />
          </label>

          <button type="submit">Complete Preparedness Profile</button>
        </form>

        <form className="preparedness-card preparedness-form" onSubmit={submitInventory}>
          <p className="section-kicker">Community Inventory</p>
          <h2>Log shared supplies</h2>

          <label>
            Supply name
            <input required value={inventory.item_name} onChange={(e) => setInventory({ ...inventory, item_name: e.target.value })} />
          </label>

          <div className="preparedness-form-row">
            <label>
              Category
              <select value={inventory.category} onChange={(e) => setInventory({ ...inventory, category: e.target.value })}>
                {["water", "food", "medical", "power", "communication", "general"].map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
            <label>
              Quantity
              <input type="number" min="0" value={inventory.quantity} onChange={(e) => setInventory({ ...inventory, quantity: e.target.value })} />
            </label>
          </div>

          <label>
            Storage location
            <input value={inventory.storage_location} onChange={(e) => setInventory({ ...inventory, storage_location: e.target.value })} />
          </label>

          <button type="submit">Log Community Supplies</button>

          <div className="preparedness-inventory-list">
            {data.inventory.length ? (
              data.inventory.map((item) => (
                <div key={`${item.category}-${item.label}`}>
                  <span>
                    {item.label}: {item.quantity}/{item.target_quantity} {item.unit}
                  </span>
                  <ProgressBar value={item.percent} />
                </div>
              ))
            ) : (
              <p>No supplies logged yet. Start with one useful item.</p>
            )}
          </div>
        </form>
      </section>

      <section className="preparedness-grid-two">
        <form className="preparedness-card preparedness-form" onSubmit={submitVolunteer}>
          <p className="section-kicker">Volunteer Coordination</p>
          <h2>Register to serve</h2>

          <label>
            Role
            <select value={volunteer.role} onChange={(e) => setVolunteer({ ...volunteer, role: e.target.value })}>
              {Object.entries(roles).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Availability
            <input value={volunteer.availability} onChange={(e) => setVolunteer({ ...volunteer, availability: e.target.value })} />
          </label>

          <label>
            Skills
            <input value={volunteer.skills} onChange={(e) => setVolunteer({ ...volunteer, skills: e.target.value })} />
          </label>

          <button type="submit">Volunteer</button>
        </form>

        <article className="preparedness-card">
          <p className="section-kicker">Community Activity</p>
          <h2>Recent cooperation</h2>
          <div className="preparedness-activity">
            {data.activity.length ? (
              data.activity.map((item) => (
                <div key={item.id}>
                  <strong>{item.title || item.text || item.message}</strong>
                  <span>{item.timestamp ? new Date(item.timestamp).toLocaleString() : "Recently"}</span>
                </div>
              ))
            ) : (
              <p>No preparedness activity yet. The first action can begin today.</p>
            )}
          </div>
        </article>
      </section>

      <section className="operation-section">
        <div>
          <p className="section-kicker">Operations Activity Pattern</p>
          <h2>Preparedness Activity Feed</h2>
        </div>
        <OperationActivityFeed activities={operationActivity} />
      </section>

      <section className="operation-section">
        <div>
          <p className="section-kicker">Reserved Operations Modules</p>
          <h2>Built to Grow Without Rewriting Preparedness</h2>
        </div>
        <div className="operation-grid">
          {futureModules.map((item) => (
            <ComingSoonOperationCard key={item.key} module={item} />
          ))}
        </div>
      </section>
    </main>
  );
}