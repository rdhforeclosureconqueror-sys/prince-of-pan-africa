import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import ResultsDashboard from "../components/leadership/ResultsDashboard";
import { fetchLeadershipDashboard } from "../services/leadershipService";
import "../styles/leadership.css";

export default function LeadershipResultsPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const userId = searchParams.get("userId") || "";

  useEffect(() => {
    let mounted = true;

    if (!userId) {
      setLoading(false);
      return () => {
        mounted = false;
      };
    }

    setLoading(true);
    fetchLeadershipDashboard(userId)
      .then((loaded) => {
        if (mounted) {
          setDashboard(loaded);
          console.info("[leadership-trace] result render source", {
            userId,
            submissionId: location.state?.submissionId || loaded?.latest?.submissionId,
            historyCount: loaded?.history?.length || 0,
          });
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [location.state?.submissionId, userId]);

  const result = dashboard?.latest || null;

  const pathway = useMemo(() => {
    if (!result?.roles) return null;
    return {
      primary: result.roles.primary,
      nextSteps: [
        `Double down on ${result.roles.primary}`,
        `Support with ${result.roles.secondary}`,
        `Train ${result.roles.growth}`,
        `Monitor ${result.roles.shadow}`,
      ],
    };
  }, [result]);

  if (loading) {
    return (
      <main className="leadership-page">
        <header>
          <h1>Loading leadership dashboard…</h1>
        </header>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="leadership-page">
        <header>
          <h1>Results unavailable</h1>
          <p>We could not find a saved dashboard for this user. Start a new assessment.</p>
        </header>
        <Link className="leadership-submit" to="/leadership">
          Start Leadership Assessment
        </Link>
      </main>
    );
  }

  return (
    <main className="leadership-page">
      <header>
        <h1>Leadership Results Dashboard</h1>
        <p>
          Saved assessment {result.assessmentId} for user {result.userId}.
        </p>
      </header>

      <section className="pathway-panel">
        <h3>Save Status</h3>
        <p>
          {dashboard.saved ? "Assessment saved and loaded from dashboard history." : "Assessment status unknown."}
        </p>
      </section>

      <ResultsDashboard result={result} />

      {pathway ? (
        <section className="pathway-panel">
          <h3>Pathway System — {pathway.primary}</h3>
          <ul>
            {pathway.nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="pathway-panel">
        <h3>Assessment History</h3>
        {dashboard.history.length ? (
          <ul>
            {dashboard.history.map((entry) => (
              <li key={entry.assessmentId}>
                {entry.assessmentId} · {entry.roles?.primary || "Unknown"} · {entry.createdAt || "No timestamp"}
              </li>
            ))}
          </ul>
        ) : (
          <p>No saved history found.</p>
        )}
      </section>

      <section className="pathway-panel">
        <h3>Start Program</h3>
        <p>Continue with the current saved assessment context.</p>
        <Link
          className="leadership-submit"
          to={`/dashboard?userId=${encodeURIComponent(result.userId)}&assessmentId=${encodeURIComponent(result.assessmentId || "")}`}
        >
          Start Program
        </Link>
      </section>
    </main>
  );
}
