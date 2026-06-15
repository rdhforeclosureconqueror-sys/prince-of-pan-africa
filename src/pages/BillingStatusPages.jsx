import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../api/api";
import "../styles/membership.css";

function BillingStatusPage({ title, detail, nextLabel, nextTo, children }) {
  return (
    <main className="membership-shell">
      <section className="membership-hero cosmic-readable-shell">
        <p className="membership-kicker">Billing</p>
        <h1>{title}</h1>
        <p className="membership-subtitle">{detail}</p>
        {children}
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
  const [state, setState] = useState({ loading: true, active: false, message: "Verifying subscription state…" });

  useEffect(() => {
    let mounted = true;
    get("/billing/status")
      .then((status) => {
        if (!mounted) return;
        if (status.active) {
          setState({ loading: false, active: true, message: `Access is active for ${status.tier}.` });
        } else {
          setState({
            loading: false,
            active: false,
            message: "Checkout returned, but backend subscription state is not active yet. Please refresh after Stripe finishes processing.",
          });
        }
      })
      .catch(() => {
        if (mounted) {
          setState({ loading: false, active: false, message: "Sign in to verify your subscription status." });
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <BillingStatusPage
      title={state.active ? "Membership access active" : "Membership billing return received"}
      detail={state.message}
      nextLabel={state.active ? "Go to Dashboard" : "Check Dashboard"}
      nextTo="/dashboard"
    >
      {state.loading && <p className="membership-kicker">Verifying with backend subscription records</p>}
    </BillingStatusPage>
  );
}

export function BillingCancelPage() {
  return (
    <BillingStatusPage
      title="Membership checkout canceled"
      detail="No payment was processed. You can restart checkout whenever you are ready."
      nextLabel="Review Membership Options"
      nextTo="/membership"
    />
  );
}
