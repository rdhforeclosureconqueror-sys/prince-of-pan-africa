import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, active: false, message: "Verifying subscription state…", nextTo: "/dashboard" });

  useEffect(() => {
    let mounted = true;
    get("/billing/status")
      .then((status) => {
        if (!mounted) return;
        if (status.active) {
          const isBuilder = status.tier === "builder_member" || status.plan === "builder";
          setState({ loading: false, active: true, message: `Access is active for ${status.tier}.`, nextTo: isBuilder ? "/builder/onboarding" : "/dashboard" });
          if (isBuilder) {
            window.setTimeout(() => navigate("/builder/onboarding"), 900);
          }
        } else {
          setState({
            loading: false,
            active: false,
            message: "Checkout returned, but backend subscription state is not active yet. Please refresh after Stripe finishes processing.",
            nextTo: "/dashboard",
          });
        }
      })
      .catch(() => {
        if (mounted) {
          setState({ loading: false, active: false, message: "Sign in to verify your subscription status.", nextTo: "/dashboard" });
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
      nextLabel={state.active ? (state.nextTo === "/builder/onboarding" ? "Start Builder Activation" : "Go to Dashboard") : "Check Dashboard"}
      nextTo={state.nextTo}
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
