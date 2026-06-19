import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAssessmentTransferToken, getAssessmentCatalog, getAssessmentResults } from "../api/assessments";
import "../styles/dashboard.css";

function normalizeCatalog(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.assessments)) return payload.assessments;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.catalog)) return payload.catalog;
  return [];
}

function assessmentKey(assessment) {
  return assessment.id || assessment.slug || assessment.key || assessment.assessment_type || assessment.type || assessment.name || assessment.title;
}

function assessmentTitle(assessment) {
  return assessment.title || assessment.name || assessment.assessment_name || "Garvey Assessment";
}

function assessmentDescription(assessment) {
  return assessment.description || assessment.summary || assessment.short_description || "A guided Garvey-powered assessment to help shape your next step.";
}

function assessmentTime(assessment) {
  const minutes = assessment.estimated_minutes || assessment.estimated_time_minutes || assessment.duration_minutes;
  if (minutes) return `${minutes} minutes`;
  return assessment.estimated_time || assessment.duration || "Time varies";
}

function assessmentCategory(assessment) {
  return assessment.category || assessment.domain || assessment.track || "Personal Development";
}

function completionFor(assessment, results) {
  const key = String(assessmentKey(assessment) || "").toLowerCase();
  return results.find((result) => {
    const candidates = [result.assessment_type, result.assessment_name, result.slug, result.id].filter(Boolean).map((item) => String(item).toLowerCase());
    return candidates.includes(key);
  });
}

function scoreFor(completion) {
  return completion?.overall_score ?? completion?.latest_score ?? null;
}

function statusFor(assessment, completion) {
  const raw = assessment.status || completion?.completion_status || (completion ? "completed" : "not_started");
  return String(raw).toLowerCase().replace(" ", "_");
}

function actionFor(status, completion) {
  if (status === "in_progress") return "Continue Assessment";
  if (status === "completed" && completion) return "View Results";
  if (status === "retake") return "Retake Assessment";
  return "Start Assessment";
}

function difficultyFor(assessment) {
  return assessment.difficulty || assessment.level || "Guided";
}

function recommendedNextFor(assessment, catalog, results) {
  const explicit = assessment.recommended_next_assessment || assessment.recommended_next || assessment.next_assessment;
  if (explicit) return typeof explicit === "string" ? explicit : assessmentTitle(explicit);
  const currentIndex = catalog.findIndex((item) => assessmentKey(item) === assessmentKey(assessment));
  const nextIncomplete = catalog.slice(currentIndex + 1).find((item) => !completionFor(item, results)) || catalog.find((item) => !completionFor(item, results) && assessmentKey(item) !== assessmentKey(assessment));
  return nextIncomplete ? assessmentTitle(nextIncomplete) : "Review your latest results";
}

export default function AssessmentCenter() {
  const [catalog, setCatalog] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startingKey, setStartingKey] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [catalogRes, resultsRes] = await Promise.all([getAssessmentCatalog(), getAssessmentResults()]);
        if (!mounted) return;
        setCatalog(normalizeCatalog(catalogRes));
        setResults(Array.isArray(resultsRes?.results) ? resultsRes.results : []);
      } catch (err) {
        if (mounted) setError(err.message || "Assessment Center is temporarily unavailable.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const latestResult = useMemo(() => results[0] || null, [results]);
  const completedCount = useMemo(() => catalog.filter((assessment) => completionFor(assessment, results)).length, [catalog, results]);
  const primaryRecommendation = useMemo(() => catalog.find((assessment) => !completionFor(assessment, results)) || catalog[0], [catalog, results]);

  const startAssessment = async (assessment) => {
    const key = assessmentKey(assessment);
    setStartingKey(key);
    setError("");
    try {
      const response = await createAssessmentTransferToken(key);
      const target = `${response.start_url}?token=${encodeURIComponent(response.token)}`;
      window.location.assign(target);
    } catch (err) {
      setError(err.message || "We could not start this assessment yet.");
      setStartingKey(null);
    }
  };

  if (loading) return <div className="admin-loading">Loading Assessment Center...</div>;

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Garvey Assessment Center</p>
        <h1>Assessment Center</h1>
        <p className="subtitle">Your primary hub for all Garvey-powered assessments. The catalog below is loaded live from Garvey, so Leadership is now one assessment among the full set.</p>
        <div className="mission-status-strip"><span>{catalog.length} assessments available</span><span>{completedCount} completed</span><span>Recommended next: {primaryRecommendation ? assessmentTitle(primaryRecommendation) : "None yet"}</span></div>
      </header>

      {error ? <section className="cosmic-section admin-error">⚠️ {error}</section> : null}

      {latestResult ? (
        <section className="cosmic-section member-hub-card member-hub-card--wide">
          <p className="section-kicker">Latest Assessment Result</p>
          <h2>{latestResult.assessment_name}</h2>
          <p><strong>Primary result:</strong> {typeof latestResult.primary_result === "string" ? latestResult.primary_result : JSON.stringify(latestResult.primary_result)}</p>
          <p><strong>Completed:</strong> {latestResult.completed_at ? new Date(latestResult.completed_at).toLocaleString() : "Recently"}</p>
          {latestResult.star_reward_eligible ? <p className="star-reward-label">STAR reward eligible · processed once through Simba participation.</p> : null}
          {latestResult.recommended_next_steps ? <pre className="data-note">{typeof latestResult.recommended_next_steps === "string" ? latestResult.recommended_next_steps : JSON.stringify(latestResult.recommended_next_steps, null, 2)}</pre> : null}
        </section>
      ) : null}

      <section className="cosmic-section member-hub-card member-hub-card--wide">
        <div className="section-heading-row">
          <div><p className="section-kicker">Live Garvey Catalog</p><h2>Available Assessments</h2></div>
          <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Dashboard</Link>
        </div>
        {catalog.length === 0 ? <p>No assessments are open right now. Check back soon.</p> : (
          <div className="builder-dashboard-grid">
            {catalog.map((assessment) => {
              const key = assessmentKey(assessment);
              const completed = completionFor(assessment, results);
              const status = statusFor(assessment, completed);
              const action = actionFor(status, completed);
              const score = scoreFor(completed);
              const recommendedNext = completed?.recommended_next_assessment?.assessment_name || recommendedNextFor(assessment, catalog, results);
              return (
                <article key={key} className="member-hub-card">
                  <p className="section-kicker">{assessmentCategory(assessment)}</p>
                  <h3>{assessmentTitle(assessment)}</h3>
                  <p>{assessmentDescription(assessment)}</p>
                  <p><strong>Estimated time:</strong> {assessmentTime(assessment)}</p>
                  <p><strong>Category:</strong> {assessmentCategory(assessment)}</p>
                  <p><strong>Difficulty:</strong> {difficultyFor(assessment)}</p>
                  <p><strong>Status:</strong> {status === "completed" ? "✅ Completed" : status === "in_progress" ? "In Progress" : "Not Started"}</p>
                  <p><strong>Last completed:</strong> {completed?.completed_at ? new Date(completed.completed_at).toLocaleDateString() : "Not yet"}</p>
                  <p><strong>Current score:</strong> {score !== null ? `${score}%` : "Not scored"}</p>
                  <p><strong>Recommended next:</strong> {recommendedNext}</p>
                  {assessment.star_reward ? <strong className="star-reward-label">STAR eligible</strong> : null}
                  <button type="button" className="member-action-btn" onClick={() => startAssessment(assessment)} disabled={startingKey === key}>
                    {startingKey === key ? "Opening..." : action}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
