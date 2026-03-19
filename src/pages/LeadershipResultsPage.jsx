import React, { useMemo } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import ResultsDashboard from "../components/leadership/ResultsDashboard";
import { getLeadershipResultByUserId } from "../services/leadershipService";
import "../styles/leadership.css";

export default function LeadershipResultsPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();

  const userId = searchParams.get("userId") || "";

  const result = useMemo(() => {
    const inMemory = location.state?.result;
    if (inMemory) return inMemory;
    if (!userId) return null;
    return getLeadershipResultByUserId(userId);
  }, [location.state, userId]);

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
