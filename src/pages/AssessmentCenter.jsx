import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { createAssessmentTransferToken, getAssessmentCatalog, getAssessmentResult, getAssessmentResults } from "../api/assessments";
import "../styles/dashboard.css";

const OFFICIAL_ASSESSMENTS = [
  ["Business Owner Assessment", "business-assessment", "business-owner"],
  ["Customer / Voice of Customer", "voice-of-customer", "customer-assessment", "voc"],
  ["Love Archetype Engine", "love-engine", "love-archetype"],
  ["Leadership Archetype Engine", "leadership-engine", "leadership-archetype"],
  ["Loyalty Archetype Engine", "loyalty-engine", "loyalty-archetype"],
  ["Youth Rite of Passage / Gates", "rite-of-passage", "gates"],
  ["K–6 Assessment MVP", "k6-assessment-mvp", "k-6", "k6"],
];

function normalizeText(value) {
  return String(value || "").toLowerCase().replace(/[–_\/]/g, "-").replace(/\s+/g, "-");
}

function isOfficialAssessment(assessment) {
  const raw = [assessment.id, assessment.slug, assessment.key, assessment.assessment_type, assessment.type, assessment.name, assessment.title, assessment.assessment_name].filter(Boolean).join(" ");
  const normalized = normalizeText(raw);
  return OFFICIAL_ASSESSMENTS.some((names) => names.some((name) => normalized.includes(normalizeText(name))));
}

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
    const candidates = [result.assessment_id, result.assessment_type, result.assessment_name, result.slug, result.id].filter(Boolean).map((item) => String(item).toLowerCase());
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
        setCatalog(normalizeCatalog(catalogRes).filter(isOfficialAssessment));
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
      const params = new URLSearchParams({ token: response.token, return_url: response.return_url || "https://simbawaujamaa.com/dashboard" });
      const target = `${response.start_url}?${params.toString()}`;
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
        <p className="member-kicker">Simba + Garvey Assessment Engine</p>
        <h1>Official Assessment Center</h1>
        <p className="subtitle">One polished assessment experience for Simba members. Garvey powers the assessment engine, while your progress and results sync back to your Simba dashboard.</p>
        <a href="https://simbawaujamaa.com/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</a>
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
          <a href="https://simbawaujamaa.com/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</a>
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
                  {String(assessmentTitle(assessment)).toLowerCase().includes("rite") || String(assessmentTitle(assessment)).toLowerCase().includes("k–6") || String(assessmentTitle(assessment)).toLowerCase().includes("k-6") ? <p className="data-note">Youth and K–6 assessments may ask a parent or guardian to confirm setup inside this official flow.</p> : null}
                  {assessment.star_reward ? <strong className="star-reward-label">STAR eligible</strong> : null}
                  {completed ? <Link className="member-action-btn member-action-btn--secondary" to={`/assessments/results/${encodeURIComponent(completed.result_id || completed.assessment_id)}`}>View Results</Link> : null}
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


export function AssessmentResultPage() {
  const { resultId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await getAssessmentResult(resultId);
        if (mounted) setResult(res?.result || null);
      } catch (err) {
        if (mounted) setError(err.message || "Result could not be loaded.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [resultId]);

  if (loading) return <div className="admin-loading">Loading result...</div>;

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Saved Garvey Result</p>
        <h1>{result?.assessment_name || "Assessment Result"}</h1>
        <p className="subtitle">This result is stored in Simba from the signed Garvey callback.</p>
        <a href="https://simbawaujamaa.com/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</a>
      </header>
      {error ? <section className="cosmic-section admin-error">⚠️ {error}</section> : (
        <section className="cosmic-section member-hub-card member-hub-card--wide">
          <p><strong>Status:</strong> {result?.completion_status || "completed"}</p>
          <p><strong>Completed:</strong> {result?.completed_at ? new Date(result.completed_at).toLocaleString() : "Recently"}</p>
          <p><strong>Score:</strong> {result?.overall_score ?? "Not scored"}</p>
          <p><strong>Primary result:</strong> {typeof result?.primary_result === "string" ? result.primary_result : JSON.stringify(result?.primary_result || {})}</p>
          <p><strong>Recommended Next:</strong> {result?.recommended_next_assessment?.assessment_name || "Return to the Assessment Center for your next step."}</p>
          <h2>Strengths</h2>
          <ul>{(result?.strengths || []).map((item) => <li key={item}>{item}</li>)}</ul>
          <h2>Recommendations</h2>
          <pre className="data-note">{typeof result?.recommended_next_steps === "string" ? result.recommended_next_steps : JSON.stringify(result?.recommended_next_steps || result?.opportunities_for_growth || [], null, 2)}</pre>
          <Link to="/assessments" className="member-action-btn">Retake or Continue Assessment Center</Link>
          <a href="https://simbawaujamaa.com/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</a>
        </section>
      )}
    </main>
  );
}
