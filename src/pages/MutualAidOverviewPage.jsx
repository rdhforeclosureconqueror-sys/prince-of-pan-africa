import React from "react";
import { Link } from "react-router-dom";
import MutualAidFundProgressCard from "../components/MutualAidFundProgressCard";
import { activationRequirements, formatMutualAidCurrency, MUTUAL_AID_ACTIVATION_THRESHOLD, MUTUAL_AID_STATUS } from "../mutualAidFundProgress";
import "../styles/mutualAid.css";

export default function MutualAidOverviewPage() {
  return (
    <main className="mutual-aid-page">
      <section className="mutual-aid-hero cosmic-readable-shell" aria-labelledby="mutual-aid-title">
        <p className="mutual-aid-kicker">Mutual Aid Society</p>
        <h1 id="mutual-aid-title">Simba Mutual Aid Society</h1>
        <p className="mutual-aid-subtitle">
          A governed community support system for care, preparedness, and resilience.
        </p>
        <div className="mutual-aid-status" aria-label="Current status">
          <span className="mutual-aid-status__dot" aria-hidden="true" />
          <span>{MUTUAL_AID_STATUS}</span>
        </div>
      </section>

      <section className="mutual-aid-grid" aria-label="Mutual Aid overview">
        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Community care overview</h2>
          <p>
            The Simba Mutual Aid Society helps members support one another through organized community care.
          </p>
          <p>
            Members may contribute to the fund in a later approved phase, request support in a later approved phase,
            nominate another member in a later approved phase, and help guide community priorities. Requests are
            reviewed under written policy and considered based on need, available funds, eligibility, documentation,
            and approval.
          </p>
          <p>
            Support is reviewed under written rules and depends on need, available funds, eligibility, documentation,
            and approval. It does not create individual stored value or member access to funds.
          </p>
        </article>

        <article className="mutual-aid-card mutual-aid-threshold">
          <h2>Activation threshold</h2>
          <p className="mutual-aid-threshold__amount">{formatMutualAidCurrency(MUTUAL_AID_ACTIVATION_THRESHOLD)}</p>
          <p>
            Live aid review begins only after the designated Mutual Aid / Community Development Fund reaches this
            amount in available or committed funding.
          </p>
        </article>

        <article className="mutual-aid-card">
          <h2>Activation requirements</h2>
          <p>Activation also requires these safeguards to be in place:</p>
          <ul className="mutual-aid-list">
            {activationRequirements.map((requirement) => (
              <li key={requirement}>{requirement}</li>
            ))}
          </ul>
        </article>

        <MutualAidFundProgressCard />

        <article className="mutual-aid-card mutual-aid-card--wide">
          <h2>Requests coming soon</h2>
          <p>
            Mutual aid requests are not active in this phase. Until activation, this page shows the purpose, launch
            path, and safeguards for the Society.
          </p>
          <p>
            No mutual aid distributions occur before activation, and no request, nomination, contribution, or review
            forms are available on this display-only page.
          </p>
        </article>
      </section>

      <section className="mutual-aid-docs cosmic-readable-shell" aria-label="Mutual Aid source documents">
        <h2>Approved source documents</h2>
        <p>This overview follows the approved Mutual Aid documentation package.</p>
        <div className="mutual-aid-docs__links">
          <Link to="/library">View Simba library</Link>
        </div>
      </section>
    </main>
  );
}
