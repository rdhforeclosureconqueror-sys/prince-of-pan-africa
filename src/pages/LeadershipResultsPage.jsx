import React, { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import ResultsDashboard from "../components/leadership/ResultsDashboard";
import { fetchLeadershipResultByUserId } from "../services/leadershipService";
import "../styles/leadership.css";

export default function LeadershipResultsPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [result, setResult] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result);

  const userId = searchParams.get("userId") || "";

  useEffect(() => {
    if (!userId || location.state?.result) return;

    let mounted = true;
    setLoading(true);
    fetchLeadershipResultByUserId(userId)
      .then((loaded) => {
        if (mounted) setResult(loaded);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [userId, location.state]);

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
        <p>User ID: {result.userId}</p>
      </header>
      <ResultsDashboard result={result} />
    </main>
  );
}
