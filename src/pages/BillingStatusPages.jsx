import React from "react";
import { Link } from "react-router-dom";
import "../styles/membership.css";

function BillingStatusPage({ title, detail, nextLabel, nextTo }) {
  return (
    <main className="membership-shell">
      <section className="membership-hero cosmic-readable-shell">
        <p className="membership-kicker">Billing</p>
        <h1>{title}</h1>
        <p className="membership-subtitle">{detail}</p>
        <div className="membership-cta-row">
          <Link to={nextTo} className="membership-btn membership-btn--gold">
            {nextLabel}
          </Link>
          <Link to="/membership" className="membership-btn membership-btn--ghost">
            Back to Membership
          </Link>
        </div>
      </section>
    </main>
  );
}

export function BillingSuccessPage() {
  return (
    <BillingStatusPage
      title="Membership billing return received"
      detail="Checkout is not live yet, and this page does not confirm payment. Future releases must verify backend subscription state before showing active access."
      nextLabel="Go to Dashboard"
      nextTo="/dashboard"
    />
  );
}

export function BillingCancelPage() {
  return (
    <BillingStatusPage
      title="Membership checkout canceled"
      detail="No payment was processed. Stripe Checkout remains disabled while the billing foundation is prepared."
      nextLabel="Review Membership Options"
      nextTo="/membership"
    />
  );
}
