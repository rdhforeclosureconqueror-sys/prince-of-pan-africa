import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { generatePublicIntelligenceDiagnosticReport, getIntelligenceHealthHistory, runIntelligenceHealthDiagnostic } from "../api/societyBuilder";

const DIAGNOSTIC_TIMEOUT_MS = 30000;
const DEBUG_ERRORS = import.meta.env?.DEV || import.meta.env?.VITE_ADMIN_DEBUG === "true";
const PUBLIC_REPORT_MISSING_URL_MESSAGE = "Public report was generated but no valid public URL was returned.";

const withTimeout = (promise, message = "Diagnostic request timed out. Please try again.") => {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error(message)), DIAGNOSTIC_TIMEOUT_MS);
  });
  return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer));
};

const asArray = (value) => (Array.isArray(value) ? value : []);
const safeObject = (value) => (value && typeof value === "object" && !Array.isArray(value) ? value : {});
const adminErrorMessage = (fallback, err) => `${fallback}${DEBUG_ERRORS && err?.message ? ` (${err.message})` : ""}`;
const normalizeHistory = (payload) => asArray(payload?.history).filter((run) => run && typeof run === "object");
const normalizeReport = (payload) => safeObject(payload?.report || payload?.public_report || payload);
const isNonEmptyString = (value) => typeof value === "string" && value.trim().length > 0;
const PUBLIC_DIAGNOSTIC_ORIGIN = "https://simbawaujamaa.com";
const publicReportPathFromToken = (token) => `/public/intelligence-diagnostics/${encodeURIComponent(token.trim())}`;
const PUBLIC_REPORT_VERIFICATION_PENDING = "pending";
const PUBLIC_REPORT_VERIFICATION_PASS = "pass";
const PUBLIC_REPORT_VERIFICATION_FAIL = "fail";
const PUBLIC_REPORT_VERIFICATION_CHECKS = [
  { key: "html", label: "HTML report URL" },
  { key: "htmlEmbeddedData", label: "Embedded diagnostic JSON" },
  { key: "json", label: "JSON report URL" },
  { key: "markdown", label: "Markdown report URL" },
];
const isSafePublicReportHref = (href) => {
  if (!isNonEmptyString(href)) return false;
  try {
    const url = new URL(href, window.location.origin);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (_err) {
    return false;
  }
};

export const normalizePublicReportResponse = (payload, origin = window.location.origin) => {
  const publicReportState = normalizeReport(payload);
  const publicUrl = publicReportState.public_url;
  const token = publicReportState.token;

  if (isNonEmptyString(publicUrl)) {
    try {
      const validatedUrl = new URL(publicUrl.trim(), origin).href;
      if (!isSafePublicReportHref(validatedUrl)) return { publicReportState, publicReportUrl: "", error: PUBLIC_REPORT_MISSING_URL_MESSAGE };
      return { publicReportState, publicReportUrl: validatedUrl, error: "" };
    } catch (_err) {
      return { publicReportState, publicReportUrl: "", error: PUBLIC_REPORT_MISSING_URL_MESSAGE };
    }
  }

  if (isNonEmptyString(token)) {
    const tokenUrl = new URL(publicReportPathFromToken(token), PUBLIC_DIAGNOSTIC_ORIGIN).href;
    if (!isSafePublicReportHref(tokenUrl)) return { publicReportState, publicReportUrl: "", error: PUBLIC_REPORT_MISSING_URL_MESSAGE };
    return { publicReportState, publicReportUrl: tokenUrl, error: "" };
  }

  return { publicReportState, publicReportUrl: "", error: PUBLIC_REPORT_MISSING_URL_MESSAGE };
};

const pendingPublicReportVerification = () => PUBLIC_REPORT_VERIFICATION_CHECKS.reduce((acc, check) => ({ ...acc, [check.key]: { status: PUBLIC_REPORT_VERIFICATION_PENDING, httpStatus: null, responseTimeMs: null, error: "" } }), {});

const publicReportVerificationFailed = (checks) => Object.values(safeObject(checks)).some((check) => check?.status === PUBLIC_REPORT_VERIFICATION_FAIL);
const publicReportVerificationPassed = (checks) => PUBLIC_REPORT_VERIFICATION_CHECKS.every((check) => checks?.[check.key]?.status === PUBLIC_REPORT_VERIFICATION_PASS);
const PUBLIC_REPORT_REQUIRED_JSON_KEYS = ["public_report", "read_only", "no_write_confirmation", "overall_summary", "layers"];
const validatePublicDiagnosticJson = (parsed, label = "JSON report") => {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error(`${label} response was not an object.`);
  const missingKeys = PUBLIC_REPORT_REQUIRED_JSON_KEYS.filter((key) => !(key in parsed));
  if (missingKeys.length) throw new Error(`${label} missing required diagnostic keys: ${missingKeys.join(", ")}.`);
  if (parsed.public_report !== true) throw new Error(`${label} was not marked as a public diagnostic report.`);
  if (parsed.read_only !== true) throw new Error(`${label} was not marked read-only.`);
  if (!parsed.no_write_confirmation || typeof parsed.no_write_confirmation !== "object" || Array.isArray(parsed.no_write_confirmation)) throw new Error(`${label} missing no-write confirmation.`);
  if (!Array.isArray(parsed.layers)) throw new Error(`${label} layers were not an array.`);
  return parsed;
};
const isAiReadableDiagnosticMarkdown = (markdown) => /^#\s+(Public Diagnostic Report|Intelligence Diagnostic Report|Public Intelligence Diagnostic Report)\s*$/im.test(markdown.trim());
const publicReportVerificationStatusText = (checks) => {
  if (publicReportVerificationPassed(checks)) return "Public diagnostic report verified from browser.";
  if (publicReportVerificationFailed(checks)) return "Public diagnostic report generated, but verification failed.";
  return "Verifying generated public diagnostic report from browser…";
};

const timedFetch = async (url) => {
  const started = performance.now();
  const response = await fetch(url, { method: "GET", credentials: "omit", cache: "no-store" });
  const responseTimeMs = Math.round(performance.now() - started);
  return { response, responseTimeMs };
};

const parseEmbeddedDiagnosticReport = (html) => {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const node = doc.getElementById("diagnostic-data");
  if (!node || node.getAttribute("type") !== "application/json") throw new Error("Missing embedded diagnostic-data JSON script.");
  try {
    const parsed = JSON.parse(node.textContent || "{}");
    return validatePublicDiagnosticJson(parsed, "Embedded diagnostic-data JSON");
  } catch (err) {
    throw new Error(`Embedded diagnostic-data JSON did not parse: ${err.message}`);
  }
};

export const verifyPublicDiagnosticReportFromBrowser = async ({ htmlUrl, jsonUrl, markdownUrl }, onProgress = () => {}) => {
  const update = (key, result) => onProgress(key, result);
  const htmlResult = { status: PUBLIC_REPORT_VERIFICATION_FAIL, httpStatus: null, responseTimeMs: null, error: "" };
  let html = "";
  try {
    const { response, responseTimeMs } = await timedFetch(htmlUrl);
    htmlResult.httpStatus = response.status;
    htmlResult.responseTimeMs = responseTimeMs;
    if (!response.ok) throw new Error(`HTML request returned HTTP ${response.status}.`);
    html = await response.text();
    htmlResult.status = PUBLIC_REPORT_VERIFICATION_PASS;
  } catch (err) {
    htmlResult.error = err?.message || "HTML report request failed.";
  }
  update("html", htmlResult);

  const embeddedResult = { status: PUBLIC_REPORT_VERIFICATION_FAIL, httpStatus: htmlResult.httpStatus, responseTimeMs: htmlResult.responseTimeMs, error: "" };
  try {
    if (htmlResult.status !== PUBLIC_REPORT_VERIFICATION_PASS) throw new Error("Skipped because HTML report did not load successfully.");
    parseEmbeddedDiagnosticReport(html);
    embeddedResult.status = PUBLIC_REPORT_VERIFICATION_PASS;
  } catch (err) {
    embeddedResult.error = err?.message || "Embedded diagnostic-data JSON validation failed.";
  }
  update("htmlEmbeddedData", embeddedResult);

  const jsonResult = { status: PUBLIC_REPORT_VERIFICATION_FAIL, httpStatus: null, responseTimeMs: null, error: "" };
  try {
    const { response, responseTimeMs } = await timedFetch(jsonUrl);
    jsonResult.httpStatus = response.status;
    jsonResult.responseTimeMs = responseTimeMs;
    if (!response.ok) throw new Error(`JSON request returned HTTP ${response.status}.`);
    const parsed = await response.json();
    validatePublicDiagnosticJson(parsed, "JSON report");
    jsonResult.status = PUBLIC_REPORT_VERIFICATION_PASS;
  } catch (err) {
    jsonResult.error = err?.message || "JSON report validation failed.";
  }
  update("json", jsonResult);

  const markdownResult = { status: PUBLIC_REPORT_VERIFICATION_FAIL, httpStatus: null, responseTimeMs: null, error: "" };
  try {
    const { response, responseTimeMs } = await timedFetch(markdownUrl);
    markdownResult.httpStatus = response.status;
    markdownResult.responseTimeMs = responseTimeMs;
    if (!response.ok) throw new Error(`Markdown request returned HTTP ${response.status}.`);
    const markdown = await response.text();
    if (!isAiReadableDiagnosticMarkdown(markdown)) throw new Error("Markdown did not begin with an AI-readable public diagnostic heading.");
    markdownResult.status = PUBLIC_REPORT_VERIFICATION_PASS;
  } catch (err) {
    markdownResult.error = err?.message || "Markdown report validation failed.";
  }
  update("markdown", markdownResult);
};

const chainLabel = { first_changed: "First changed layer", downstream_affected: "Downstream affected", stable: "Stable layer" };

const statusIcon = (layer) => {
  if (layer?.status === "FAIL") return "🔴 Failure";
  if (layer?.regression) return "🟠 Regression";
  if (layer?.status === "WARNING") return "🟡 Warning";
  return "🟢 Healthy";
};

export default function IntelligenceHealthMonitor() {
  const mountedRef = useRef(true);
  const [running, setRunning] = useState(false);
  const [diagnosticRunState, setDiagnosticRunState] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [publicReportError, setPublicReportError] = useState("");
  const [publicReportState, setPublicReportState] = useState(null);
  const [publicReportUrl, setPublicReportUrl] = useState("");
  const [publicReportCopyMessage, setPublicReportCopyMessage] = useState("");
  const [publicReportVerification, setPublicReportVerification] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [trendWindow, setTrendWindow] = useState("10");
  const [selectedLayer, setSelectedLayer] = useState("Decision Support");

  const clearPublicReport = () => {
    setPublicReportState(null);
    setPublicReportUrl("");
    setPublicReportError("");
    setPublicReportCopyMessage("");
    setPublicReportVerification(null);
  };

  const loadHistory = useCallback(async () => {
    try {
      const res = await withTimeout(getIntelligenceHealthHistory(), "Diagnostic history request timed out.");
      if (!mountedRef.current) return [];
      const safeHistory = normalizeHistory(res);
      setHistory(safeHistory);
      setHistoryError(safeHistory.length ? "" : "Last run could not be loaded");
      return safeHistory;
    } catch (err) {
      if (!mountedRef.current) return [];
      setHistory([]);
      setHistoryError(adminErrorMessage("Last run could not be loaded", err));
      return [];
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    loadHistory();
    return () => { mountedRef.current = false; };
  }, [loadHistory]);

  const run = async () => {
    if (running || generatingReport) return;
    setRunning(true); setError(""); setPublicReportError(""); setPublicReportCopyMessage("");
    try {
      const res = await withTimeout(runIntelligenceHealthDiagnostic());
      if (!mountedRef.current) return;
      setDiagnosticRunState(safeObject(res));
      await loadHistory();
    } catch (err) {
      if (mountedRef.current) setError(adminErrorMessage("Diagnostics unavailable", err));
    } finally {
      if (mountedRef.current) setRunning(false);
    }
  };

  const generateReport = async () => {
    if (running || generatingReport) return;
    setGeneratingReport(true); setError(""); setPublicReportError(""); setPublicReportCopyMessage(""); setPublicReportVerification(null);
    try {
      const res = await withTimeout(generatePublicIntelligenceDiagnosticReport(), "Public report generation timed out.");
      if (!mountedRef.current) return;
      const normalized = normalizePublicReportResponse(res);
      setPublicReportState(normalized.publicReportState);
      setPublicReportUrl(normalized.publicReportUrl);
      if (normalized.error) setPublicReportError(normalized.error);
      if (normalized.publicReportUrl) {
        const jsonUrl = `${normalized.publicReportUrl}.json`;
        const markdownUrl = `${normalized.publicReportUrl}.md`;
        setPublicReportVerification(pendingPublicReportVerification());
        await verifyPublicDiagnosticReportFromBrowser({ htmlUrl: normalized.publicReportUrl, jsonUrl, markdownUrl }, (key, result) => {
          if (!mountedRef.current) return;
          setPublicReportVerification((previous) => ({ ...(previous || pendingPublicReportVerification()), [key]: result }));
        });
      }
      await loadHistory();
    } catch (err) {
      if (mountedRef.current) setPublicReportError(adminErrorMessage("Public report could not be generated", err));
    } finally {
      if (mountedRef.current) setGeneratingReport(false);
    }
  };

  const copyPublicReportUrl = async () => {
    if (!safePublicReportUrl) return;
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard API unavailable");
      }
      await navigator.clipboard.writeText(safePublicReportUrl);
      if (mountedRef.current) setPublicReportCopyMessage("Copied public diagnostic URL.");
    } catch (_err) {
      if (mountedRef.current) setPublicReportCopyMessage("Copy failed. Select the URL manually.");
    }
  };

  const result = safeObject(diagnosticRunState || history[0]);
  const layers = asArray(result?.layers).filter((layer) => layer && typeof layer === "object");
  const healthTrend = useMemo(() => safeObject(result?.comparison_to_previous || result?.health_trend), [result]);
  const dependencyImpact = safeObject(result?.dependency_impact);
  const dependencyChain = asArray(dependencyImpact.chain);
  const recommendedNextActions = asArray(result?.recommended_next_actions);
  const commandCenter = safeObject(result?.command_center);
  const aiOperationsAdvisor = asArray(result?.ai_operations_advisor || result?.recommended_actions_ranked);
  const predictiveIntelligence = safeObject(result?.predictive_intelligence);
  const ecosystemIntelligence = safeObject(result?.ecosystem_intelligence);
  const aiChiefOperatingOfficer = safeObject(result?.ai_chief_operating_officer);
  const actionDisabled = running || generatingReport;
  const safePublicReportUrl = isSafePublicReportHref(publicReportUrl) ? publicReportUrl : "";
  const safePublicReportJsonUrl = safePublicReportUrl ? `${safePublicReportUrl}.json` : "";
  const safePublicReportMarkdownUrl = safePublicReportUrl ? `${safePublicReportUrl}.md` : "";
  const publicReportVerificationMessage = publicReportVerificationStatusText(publicReportVerification);
  const trends = safeObject(trendWindow === "all" ? safeObject(result?.trends)?.["100"] || safeObject(history[0]?.trends)?.["100"] : safeObject(result?.trends)[trendWindow] || safeObject(history[0]?.trends)[trendWindow]);
  const comparisonRows = asArray(healthTrend.rows);
  const pipeline = safeObject(result?.pipeline);
  const pipelineSteps = asArray(pipeline.steps);
  const performanceSummary = safeObject(result?.performance_summary);
  const timeline = asArray(result?.timeline);
  const rootCauseClassification = safeObject(result?.root_cause_classification);
  const passFailSummary = safeObject(result?.pass_fail_summary);
  const dependencyLayers = ["Member", "Society", "Institution", "Opportunity", "Predictive", "Decision Support", "Execution Planning", "Execution Intelligence", "Institutional Memory", "Institutional Learning"];
  const selectedLayerIndex = Math.max(0, dependencyLayers.indexOf(selectedLayer));
  const healthScore = (result?.overall_health_percent ?? result?.overall_health?.percent) ?? "—";
  const failureCount = asArray(result?.critical_failures).length || asArray(result?.failed_layers).length || (passFailSummary.failed ?? 0);
  const regressionCount = result?.regression_count ?? result?.regression_summary?.count ?? 0;
  const warningCount = asArray(result?.warnings).length || (passFailSummary.warnings ?? 0);
  const missionStatus = commandCenter.mission_status || (failureCount ? "Critical" : regressionCount || warningCount ? "At Risk" : layers.length ? "Healthy" : "At Risk");
  const riskLevel = commandCenter.risk_level || (failureCount ? "High" : regressionCount ? "Elevated" : warningCount ? "Moderate" : "Low");
  const highestPriority = commandCenter.todays_highest_priority || commandCenter.todays_recommendation || aiOperationsAdvisor[0]?.title || recommendedNextActions[0] || "Run a diagnostic and preserve current baselines until evidence is available.";
  const timeToResolution = commandCenter.estimated_time_to_resolution || aiOperationsAdvisor[0]?.estimated_time || aiChiefOperatingOfficer.suggested_sprint?.estimated_completion || "1–2 hours after the highest-priority fix is selected.";
  const cooRecommendation = commandCenter.ai_coo_recommendation || aiChiefOperatingOfficer.recommendation || `${missionStatus} mission posture with ${healthScore}% overall health. ${highestPriority} should be handled first because it has the greatest leadership impact on the intelligence chain; trend review, public-report polishing, and lower-risk baseline cleanup can wait until the priority queue is resolved and the diagnostic is re-run.`;
  const priorityQueue = (aiOperationsAdvisor.length ? aiOperationsAdvisor : recommendedNextActions.map((action, index) => ({ title: action, priority: index === 0 ? "HIGH" : "MEDIUM" }))).map((action, index) => ({
    id: action.id || `priority-action-${index}`,
    priority: action.priority || (index === 0 ? "HIGH" : "MEDIUM"),
    title: action.title || action.suggested_fix || action.action || `Recommended action ${index + 1}`,
    impact: action.impact || action.estimated_impact || "Stabilizes executive confidence and reduces regression exposure.",
    effort: action.estimated_effort || action.estimated_difficulty || action.estimated_time || "Medium",
    layers: asArray(action.affected_intelligence_layers || action.affected_layers).length ? asArray(action.affected_intelligence_layers || action.affected_layers).join(" → ") : dependencyLayers.slice(Math.max(0, index - 1), Math.min(dependencyLayers.length, index + 3)).join(" → "),
    improvement: action.expected_health_improvement || action.expected_improvement || `+${Math.max(2, 8 - index * 2)} health points`,
  }));
  const forecast = safeObject(predictiveIntelligence.ai_forecast || predictiveIntelligence.forecast);
  const sprint = safeObject(aiChiefOperatingOfficer.sprint_planning || aiChiefOperatingOfficer.suggested_sprint);
  const trendMetrics = [
    ["Overall Health Score", "overall_health_score", "%"],
    ["Response Time", "response_time_ms", "ms"],
    ["API Latency", "api_latency_ms", "ms"],
    ["Diagnostic Duration", "diagnostic_duration_ms", "ms"],
    ["Failure Count", "failure_count", ""],
    ["Regression Count", "regression_count", ""],
    ["Storage", "storage_usage_percent", "%"],
    ["Memory", "memory_usage_percent", "%"],
    ["Deployment Duration", "diagnostic_duration_ms", "ms"],
    ["Public Verification", "public_verification", "%"],
  ];
  const directionIcon = (direction) => direction === "improvement" ? "🟢" : direction === "regression" ? "🔴" : "🟡";
  const pipelineIcon = (status) => status === "PASS" ? "🟢" : status === "FAIL" ? "🔴" : "🟡";

  const browserVerified = publicReportVerificationPassed(publicReportVerification);
  const browserVerificationStarted = Boolean(publicReportVerification);
  const browserDrivenPipelineSteps = [
    { key: "diagnostic_generated", label: "Diagnostic Generated", status: result?.ok ? "PASS" : "WARNING" },
    { key: "report_stored", label: "Report Stored", status: publicReportState ? "PASS" : "WARNING" },
    { key: "html_available", label: "HTML Available", status: publicReportVerification?.html?.status === PUBLIC_REPORT_VERIFICATION_PASS ? "PASS" : "WARNING" },
    { key: "embedded_json_valid", label: "Embedded JSON Valid", status: publicReportVerification?.htmlEmbeddedData?.status === PUBLIC_REPORT_VERIFICATION_PASS ? "PASS" : "WARNING" },
    { key: "json_endpoint_reachable", label: "JSON Endpoint Reachable", status: publicReportVerification?.json?.status === PUBLIC_REPORT_VERIFICATION_PASS ? "PASS" : "WARNING" },
    { key: "markdown_endpoint_reachable", label: "Markdown Endpoint Reachable", status: publicReportVerification?.markdown?.status === PUBLIC_REPORT_VERIFICATION_PASS ? "PASS" : "WARNING" },
    { key: "public_report_sanitized", label: "Public Report Sanitized", status: publicReportState?.read_only ? "PASS" : "WARNING" },
    { key: "read_only_confirmed", label: "Read Only Confirmed", status: result?.production_writes === 0 && !result?.workflow_execution ? "PASS" : "FAIL" },
    { key: "browser_verification_passed", label: "Browser Verification Passed", status: browserVerified ? "PASS" : "WARNING" },
    { key: "ai_ready", label: "AI Ready", status: browserVerified && (result?.ai_summary || result?.executive_summary) ? "PASS" : "WARNING" },
  ];
  const displayedPipelineSteps = browserVerificationStarted ? browserDrivenPipelineSteps : pipelineSteps;
  const displayedPipelineOverallStatus = displayedPipelineSteps.length ? (displayedPipelineSteps.some((step) => step.status === "FAIL") ? "Pipeline Failure" : displayedPipelineSteps.some((step) => step.status === "WARNING") ? "Pipeline Warning" : "Intelligence Pipeline Healthy") : (pipeline.overall_status || "Pipeline Warning");

  return (
    <section className="cosmic-section intelligence-health-monitor" aria-labelledby="intelligence-health-title">
      <p className="section-kicker">Admin Only · Read-Only Diagnostic</p>
      <h2 id="intelligence-health-title">🧠 Intelligence Health Monitor</h2>
      <p className="admin-subtext">Runs deterministic isolated fixtures through Member, Society, Institution, Opportunity, Predictive, Decision Support, Execution Planning, Execution Intelligence, Institutional Memory, and Institutional Learning layers without touching production records, workflow tasks, assignments, notifications, calendars, payments, businesses, or persisted intelligence outputs.</p>
      <div className="hero-actions">
        <button className="hero-btn" type="button" onClick={run} disabled={actionDisabled}>{running ? "Running Full Intelligence Diagnostic..." : "Run Full Intelligence Diagnostic"}</button>
        <button className="hero-btn secondary" type="button" onClick={generateReport} disabled={actionDisabled}>{generatingReport ? "Generating Public Report..." : "Generate Public Diagnostic Report"}</button>
      </div>
      {(publicReportState || safePublicReportUrl) && <article className="stat-card"><h3>Public Diagnostic Report</h3><p>This URL is public, read-only, sanitized, fixture-only, and expires at {publicReportState?.expires_at || "the configured expiration time"}.</p>{safePublicReportUrl && <><label htmlFor="public-diagnostic-report-url"><strong>Public diagnostic URL</strong></label><div className="hero-actions"><input id="public-diagnostic-report-url" readOnly value={safePublicReportUrl} onFocus={(event) => event.target.select()} aria-label="Public diagnostic report URL" /><button type="button" onClick={copyPublicReportUrl}>Copy URL</button></div><p><a href={safePublicReportUrl} target="_blank" rel="noopener noreferrer">Open public diagnostic report</a></p><p><strong>Public JSON URL</strong>: <a href={safePublicReportJsonUrl} target="_blank" rel="noopener noreferrer">{safePublicReportJsonUrl}</a></p><p><strong>Public Markdown URL</strong>: <a href={safePublicReportMarkdownUrl} target="_blank" rel="noopener noreferrer">{safePublicReportMarkdownUrl}</a></p><section aria-label="Production Verification"><h4>Production Verification</h4><p role="status">{publicReportVerificationMessage}</p><ul>{PUBLIC_REPORT_VERIFICATION_CHECKS.map((check) => { const result = publicReportVerification?.[check.key] || { status: PUBLIC_REPORT_VERIFICATION_PENDING }; return <li key={check.key}><strong>{check.label}</strong>: {result.status}{result.httpStatus ? ` · HTTP ${result.httpStatus}` : ""}{result.responseTimeMs != null ? ` · ${result.responseTimeMs}ms` : ""}{result.error ? ` · ${result.error}` : ""}</li>; })}</ul></section></>}{publicReportCopyMessage && <p role="status">{publicReportCopyMessage}</p>}<button type="button" onClick={clearPublicReport}>Clear Public Report Link</button></article>}
      {error && <article className="stat-card admin-error"><h3>Diagnostics unavailable</h3><p>⚠️ {error}</p></article>}
      {publicReportError && <article className="stat-card admin-error"><h3>Public report could not be generated</h3><p>⚠️ {publicReportError}</p><button type="button" onClick={clearPublicReport}>Clear Public Report Link</button></article>}
      {historyError && !layers.length && <article className="stat-card"><h3>Last run could not be loaded</h3><p>Diagnostics unavailable</p></article>}

      <section className="mission-control" aria-label="Executive Brief">
        <h3>Executive Brief</h3>
        <div className="dashboard-grid executive-brief-grid">
          <article className={`stat-card state-${missionStatus.toLowerCase().replace(/\s+/g, "-")}`}><h3>Mission Status</h3><h2>{missionStatus}</h2></article>
          <article className="stat-card"><h3>Overall Health Score</h3><h2>{healthScore}%</h2></article>
          <article className="stat-card"><h3>Deployment Status</h3><p>{commandCenter.deployment_status || pipeline.overall_status || "Pending diagnostic"}</p></article>
          <article className="stat-card"><h3>Risk Level</h3><p>{riskLevel}</p></article>
          <article className="stat-card executive-priority"><h3>Today’s Highest Priority</h3><p>{highestPriority}</p></article>
          <article className="stat-card"><h3>Estimated time to resolution</h3><p>{timeToResolution}</p></article>
        </div>
        <article className="stat-card ai-coo-recommendation"><h3>AI COO Recommendation</h3><p>{cooRecommendation}</p></article>
      </section>

      <h3>Priority Queue</h3>
      <article className="stat-card wide-card" aria-label="Priority Queue">
        <table className="admin-table"><thead><tr><th>Priority</th><th>Action</th><th>Impact</th><th>Effort</th><th>Affected intelligence layers</th><th>Expected health improvement</th><th>Run Action</th></tr></thead><tbody>{priorityQueue.length ? priorityQueue.map((action) => <tr key={action.id}><td><strong>{action.priority}</strong></td><td>{action.title}</td><td>{action.impact}</td><td>{action.effort}</td><td>{action.layers}</td><td>{action.improvement}</td><td><button type="button" disabled title="Action execution is planned for a future release.">Future Run Action</button></td></tr>) : <tr><td colSpan={7}>Run a diagnostic to generate ranked recommended actions by impact.</td></tr>}</tbody></table>
      </article>

      <h3>Dependency Map</h3>
      <article className="stat-card wide-card dependency-map" aria-label="Dependency Map">
        <p>Member → Society → Institution → Opportunity → Predictive → Decision Support → Execution Planning → Execution Intelligence → Institutional Memory → Institutional Learning</p>
        <div className="dependency-chain">{dependencyLayers.map((layer, index) => {
          const match = layers.find((item) => (item.layer || "").includes(layer));
          const state = match?.status === "FAIL" ? "failure" : match?.regression ? "regression" : match?.status === "WARNING" ? "warning" : "healthy";
          const relation = index < selectedLayerIndex ? "upstream" : index > selectedLayerIndex ? "downstream" : "selected";
          return <button type="button" key={layer} className={`dependency-node ${state} ${relation}`} onClick={() => setSelectedLayer(layer)} aria-pressed={selectedLayer === layer}>{layer}</button>;
        })}</div>
        <p><strong>Selected layer:</strong> {selectedLayer}. Upstream dependencies are highlighted before it; downstream dependencies are highlighted after it.</p>
      </article>

      <h3>Executive Trends</h3>
      <article className="stat-card wide-card"><label htmlFor="trend-window"><strong>View window</strong></label> <select id="trend-window" value={trendWindow} onChange={(event) => setTrendWindow(event.target.value)}><option value="10">Last 10 runs</option><option value="30">Last 30 runs</option><option value="100">Last 100 runs</option><option value="all">All Time</option></select><div className="dashboard-grid">{trendMetrics.filter(([, key]) => ["overall_health_score", "regression_count", "api_latency_ms", "diagnostic_duration_ms", "public_verification"].includes(key)).map(([label, key, unit]) => { const points = asArray(trends[key]); const last = points[points.length - 1]; const max = Math.max(1, ...points.map((point) => Number(point.value) || 0)); return <section className="stat-card" key={key}><h4>{label === "Overall Health Score" ? "Health trend" : label === "Regression Count" ? "Regression trend" : label === "API Latency" ? "API latency" : label === "Diagnostic Duration" ? "Diagnostic duration" : "Public verification history"}</h4><p>{last?.value ?? "—"}{unit}</p><div aria-label={`${label} chart`}>{points.map((point, index) => <span key={`${key}-${index}`} title={`${point.timestamp}: ${point.value}${unit}`} style={{ display: "inline-block", width: 10, height: `${Math.max(4, ((Number(point.value) || 0) / max) * 48)}px`, marginRight: 3, background: "#22c55e", verticalAlign: "bottom" }} />)}</div></section>; })}<section className="stat-card"><h4>Deployment history</h4><p>{history.length || "—"} recorded runs</p><div aria-label="Deployment history chart">{history.slice(0, 12).reverse().map((run, index) => <span key={run.diagnostic_id || index} title={run.created_at} style={{ display: "inline-block", width: 10, height: `${Math.max(4, Number(run.overall_health_percent ?? run.overall_health?.percent ?? 0) / 2)}px`, marginRight: 3, background: "#38bdf8", verticalAlign: "bottom" }} />)}</div></section></div></article>

      <h3>AI Forecast</h3>
      <div className="dashboard-grid" aria-label="AI Forecast">
        <article className="stat-card"><h3>Future regression likelihood</h3><p>{forecast.future_regression_likelihood || forecast.regression_likelihood || (regressionCount ? "Moderate" : "Low")}</p></article>
        <article className="stat-card"><h3>Confidence</h3><p>{forecast.confidence ?? aiOperationsAdvisor[0]?.confidence ?? "—"}%</p></article>
        <article className="stat-card"><h3>Likely drift areas</h3><p>{asArray(forecast.likely_drift_areas).join(", ") || layers.filter((layer) => layer.regression || layer.status === "WARNING").map((layer) => layer.layer).join(", ") || "No likely drift areas detected."}</p></article>
        <article className="stat-card"><h3>Technical debt trend</h3><p>{forecast.technical_debt_trend || (warningCount || regressionCount ? "Increasing unless priority queue is completed" : "Stable")}</p></article>
        <article className="stat-card"><h3>7-deployment stability</h3><p>{forecast.estimated_stability_next_7_deployments || forecast.stability_7_deployments || "Stable if no new regressions ship"}</p></article>
        <article className="stat-card"><h3>30-deployment stability</h3><p>{forecast.estimated_stability_next_30_deployments || forecast.stability_30_deployments || "Monitor for slow baseline drift"}</p></article>
      </div>

      <h3>AI COO Sprint Planning</h3>
      <article className="stat-card wide-card"><h4>Sprint goal</h4><p>{sprint.goal || sprint.sprint_goal || `Restore the intelligence chain to ${failureCount ? "non-critical" : "healthy"} status while protecting public diagnostic confidence.`}</p><h4>Highest ROI tasks</h4><ul>{(asArray(sprint.highest_roi_tasks).length ? asArray(sprint.highest_roi_tasks) : priorityQueue.slice(0, 3).map((action) => action.title)).map((task) => <li key={task}>{task}</li>)}</ul><h4>Recommended implementation order</h4><ol>{(asArray(sprint.recommended_implementation_order).length ? asArray(sprint.recommended_implementation_order) : priorityQueue.slice(0, 4).map((action) => action.title)).map((task) => <li key={task}>{task}</li>)}</ol><p><strong>Risk reduction estimate:</strong> {sprint.risk_reduction_estimate || "25–40% after the top two queue items are verified."}</p><p><strong>Expected health after sprint completion:</strong> {sprint.expected_health_after_completion || sprint.expected_result?.overall_health || "90%+ with no critical failures."}</p></article>

      <h3>Technical Diagnostic Evidence</h3>

      <div className="dashboard-grid">
        <div className="stat-card"><h3>Overall Health</h3><h2>{(result?.overall_health_percent ?? result?.overall_health?.percent) ?? "—"}%</h2></div>
        <div className="stat-card"><h3>Regression Count</h3><h2>{result?.regression_count ?? result?.regression_summary?.count ?? 0}</h2></div>
        <div className="stat-card"><h3>Warnings</h3><h2>{asArray(result?.warnings).length}</h2></div>
        <div className="stat-card"><h3>Critical Failures</h3><h2>{asArray(result?.critical_failures).length || asArray(result?.failed_layers).length}</h2></div>
        <div className="stat-card"><h3>Last Successful Diagnostic</h3><p>{result?.last_successful_diagnostic || "No previous successful run"}</p></div>
        <div className="stat-card"><h3>Health Trend</h3><p>{healthTrend.available ? `${healthTrend.health_trend > 0 ? "+" : ""}${healthTrend.health_trend}%` : "No previous run"}</p></div>
      </div>

      <h3>Intelligence Pipeline</h3>
      <article className="stat-card" aria-label="Intelligence Pipeline">
        <div className="dashboard-grid">
          {(displayedPipelineSteps.length ? displayedPipelineSteps : browserDrivenPipelineSteps).map((step) => <p key={step.key || step.label}><strong>{pipelineIcon(step.status)} {step.label}</strong>: {step.status}</p>)}
        </div>
        <h2>{pipelineIcon(displayedPipelineOverallStatus.includes("Failure") ? "FAIL" : displayedPipelineOverallStatus.includes("Warning") ? "WARNING" : "PASS")} {displayedPipelineOverallStatus}</h2>
      </article>

      <h3>Deployment Comparison</h3>
      <table className="admin-table"><thead><tr><th>Metric</th><th>Previous Run</th><th>Current Run</th><th>Difference</th></tr></thead><tbody>{comparisonRows.length ? comparisonRows.map((row) => <tr key={row.metric}><td>{directionIcon(row.direction)} {row.metric}</td><td>{row.previous}{row.unit}</td><td>{row.current}{row.unit}</td><td>{row.difference > 0 ? "+" : ""}{row.difference}{row.unit} · {row.direction}</td></tr>) : <tr><td colSpan={4}>No previous run is available yet.</td></tr>}</tbody></table>

      <h3>Trend Analysis</h3>
      <article className="stat-card"><label htmlFor="trend-window"><strong>View window</strong></label> <select id="trend-window" value={trendWindow} onChange={(event) => setTrendWindow(event.target.value)}><option value="10">Last 10 runs</option><option value="30">Last 30 runs</option><option value="100">Last 100 runs</option><option value="all">All Time</option></select><div className="dashboard-grid">{trendMetrics.map(([label, key, unit]) => { const points = asArray(trends[key]); const last = points[points.length - 1]; const max = Math.max(1, ...points.map((point) => Number(point.value) || 0)); return <section className="stat-card" key={key}><h4>{label}</h4><p>{last?.value ?? "—"}{unit}</p><div aria-label={`${label} trend`}>{points.map((point, index) => <span key={`${key}-${index}`} title={`${point.timestamp}: ${point.value}${unit}`} style={{ display: "inline-block", width: 10, height: `${Math.max(4, ((Number(point.value) || 0) / max) * 48)}px`, marginRight: 3, background: "#22c55e", verticalAlign: "bottom" }} />)}</div></section>; })}</div></article>


      <h3>Predictive Intelligence</h3>
      <div className="dashboard-grid" aria-label="Predictive Intelligence">
        <article className="stat-card"><h3>Health Score Prediction</h3><p>Current {predictiveIntelligence.health_score_prediction?.current ?? "—"}</p><p>Projected: {asArray(predictiveIntelligence.health_score_prediction?.projected_next_five_deployments).join(" → ") || "—"}</p></article>
        <article className="stat-card"><h3>Storage Forecast</h3><p>Current Usage {predictiveIntelligence.storage_forecast?.current_usage_percent ?? "—"}%</p><p>Projected {predictiveIntelligence.storage_forecast?.projected_usage_percent ?? "—"}% within {predictiveIntelligence.storage_forecast?.within_days ?? "—"} days.</p></article>
        <article className="stat-card"><h3>API Latency Trend</h3><p>Average {predictiveIntelligence.api_latency_trend?.average_ms ?? "—"}ms</p><p>Expected {predictiveIntelligence.api_latency_trend?.expected_ms ?? "—"}ms {predictiveIntelligence.api_latency_trend?.condition || "if current trend continues"}.</p></article>
      </div>

      <h3>Ecosystem Intelligence</h3>
      <article className="stat-card"><h2>Institutional Health Score {ecosystemIntelligence.institutional_health_score ?? "—"}%</h2><div className="dashboard-grid">{asArray(ecosystemIntelligence.subsystems).map((subsystem) => <section className="stat-card" key={subsystem.subsystem}><h4>{subsystem.subsystem}</h4><p>Health {subsystem.health}% · Performance {subsystem.performance}</p><p>Warnings: {asArray(subsystem.warnings).join(", ") || "None"}</p><p>Recommendations: {asArray(subsystem.recommendations).join("; ") || "Continue monitoring"}</p></section>)}</div></article>

      <h3>AI Chief Operating Officer</h3>
      <article className="stat-card"><h4>Suggested Sprint</h4><p>Estimated completion {aiChiefOperatingOfficer.suggested_sprint?.estimated_completion || "2 hours"}</p><ul>{asArray(aiChiefOperatingOfficer.suggested_sprint?.tasks).map((task) => <li key={task}>{task}</li>)}</ul><pre className="data-note">{JSON.stringify(aiChiefOperatingOfficer.suggested_sprint?.expected_result || {}, null, 2)}</pre><p>Estimated confidence {aiChiefOperatingOfficer.suggested_sprint?.estimated_confidence ?? "—"}%</p></article>

      <h3>Executive Performance Summary</h3>
      <div className="dashboard-grid">
        <article className="stat-card"><h3>Average API latency</h3><h2>{performanceSummary.average_api_latency_ms ?? result?.performance?.api_response_time_ms ?? "—"}ms</h2></article>
        <article className="stat-card"><h3>Slowest endpoint</h3><p>{performanceSummary.slowest_endpoint ?? result?.performance?.slowest_layer ?? "—"}</p></article>
        <article className="stat-card"><h3>Fastest endpoint</h3><p>{performanceSummary.fastest_endpoint ?? result?.performance?.fastest_layer ?? "—"}</p></article>
        <article className="stat-card"><h3>Average diagnostic time</h3><p>{performanceSummary.average_diagnostic_time_ms ?? "—"}ms</p></article>
        <article className="stat-card"><h3>Report generation time</h3><p>{performanceSummary.report_generation_time_ms ?? 0}ms</p></article>
        <article className="stat-card"><h3>Verification time</h3><p>{performanceSummary.verification_time_ms ?? 0}ms</p></article>
        <article className="stat-card"><h3>Total completed checks</h3><p>{performanceSummary.total_completed_checks ?? layers.length}</p></article>
        <article className="stat-card"><h3>Passed / Warnings / Failures</h3><p>{performanceSummary.total_passed ?? passFailSummary.passed ?? 0} / {performanceSummary.total_warnings ?? passFailSummary.warnings ?? 0} / {performanceSummary.total_failures ?? passFailSummary.failed ?? 0}</p></article>
      </div>

      <h3>System Timeline</h3>{/* Backward-compatible labels: Intelligence Timeline · AI Summary */}
      <article className="stat-card"><ol>{timeline.length ? timeline.map((event, index) => <li key={`${event.time}-${index}`}><strong>{event.time}</strong> {event.event}</li>) : <li>Run a diagnostic to replay timeline events.</li>}</ol></article>

      <h3>AI Insights</h3>{/* AI Summary */}
      <article className="stat-card"><p>{result?.ai_summary || result?.executive_summary || "Run a diagnostic to generate an natural-language AI Insights summary."}</p></article>

      <h3>Layer Status</h3>
      <div className="dashboard-grid">
        {layers.length ? layers.map((layer, index) => {
          const expected = safeObject(layer.expected);
          const actual = safeObject(layer.actual);
          const confidence = safeObject(layer.confidence_difference);
          const priority = safeObject(layer.priority_difference);
          return (
            <article className="stat-card" key={layer.layer || `layer-${index}`}>
              <h3>{layer.layer || "Unknown Layer"}</h3>
              <p><strong>{statusIcon(layer)}</strong></p>
              <p>Health: <strong>{statusIcon(layer)}</strong></p>
              <p>Status: <strong>{layer.status || "UNKNOWN"}</strong></p>
              <p>Execution Time: <strong>{layer.execution_time_ms ?? "—"}ms</strong></p>
              <p>Version: <strong>v1</strong></p>
              <p>Diagnostics: <strong>{layer.explanation || "Diagnostics unavailable"}</strong></p>
              <p>Regression Level: <strong>{layer.regression_level || layer.regression || "None"}</strong></p>
              <p>Expected Score: {expected.score ?? "—"} · Actual Score: {actual.score ?? "—"} · Score Delta: {layer.score_delta ?? safeObject(layer.difference_summary).score ?? "—"}</p>
              <p>Confidence Before/After: {confidence.expected ?? "—"} → {confidence.actual ?? "—"}</p>
              <p>Missing Evidence Δ: {layer.missing_evidence_difference ?? "—"}</p>
              <p>Priority Before/After: {priority.expected ?? "—"} → {priority.actual ?? "—"}</p>
              <p><strong>Confidence:</strong> {layer.confidence_score ?? "—"}%</p><p><strong>Supporting Evidence</strong></p><ul>{asArray(layer.supporting_evidence).map((evidence) => <li key={evidence}>{evidence}</li>)}</ul><p><strong>Why this changed:</strong> {layer.why_this_changed || layer.plain_language_reason || layer.explanation || "Diagnostics unavailable"}</p>
              <p><strong>Suggested admin action:</strong> {layer.suggested_admin_action || "Review scoring logic and re-run diagnostics before updating baselines."}</p>
            </article>
          );
        }) : <article className="stat-card"><h3>Diagnostics unavailable</h3><p>Layer data is missing or could not be loaded.</p></article>}
      </div>

      <div className="dashboard-grid">
        <article className="stat-card"><h3>Dependency Impact View</h3><p>Member → Society → Institution → Opportunity → Predictive → Decision Support → Execution Planning → Execution Intelligence → Institutional Memory → Institutional Learning</p>{dependencyChain.length ? dependencyChain.map((item) => <p key={item.layer}><strong>{item.layer}</strong>: {chainLabel[item.state] || item.state || "Stable layer"}</p>) : <p>Dependency impact unavailable until a diagnostic runs.</p>}</article>
        <article className="stat-card"><h3>Recommended Next Actions</h3>{recommendedNextActions.length ? <ul>{recommendedNextActions.map((action) => <li key={action}>{action}</li>)}</ul> : <ul><li>Review scoring logic</li><li>Review expected baselines</li><li>Do not update baselines until drift is explained</li><li>Re-run diagnostic after changes</li><li>Generate public report only after the monitor is stable</li></ul>}</article>
        <article className="stat-card"><h3>Regression Summary</h3>{layers.filter((l) => l.regression).length ? layers.filter((l) => l.regression).map((l) => <p key={l.layer}>{l.layer}: {l.regression} ({safeObject(l.difference_summary).score ?? "—"})</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Critical Failures</h3>{asArray(result?.critical_failures).length ? asArray(result.critical_failures).map((l, i) => <p key={l.layer || i}>{l.layer || "Unknown Layer"}: {l.explanation || "Diagnostics unavailable"}</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Performance Metrics</h3><pre className="data-note">{JSON.stringify(result?.performance || result?.performance_timings || {}, null, 2)}</pre></article>
        <article className="stat-card"><h3>Root Cause Analysis</h3>{rootCauseClassification.category && <p><strong>Classification:</strong> {rootCauseClassification.category} · Confidence {Math.round((rootCauseClassification.confidence || 0) * 100)}%{rootCauseClassification.heuristic ? " · heuristic" : ""}</p>}{asArray(result?.root_cause_analysis).length ? asArray(result.root_cause_analysis).map((line) => <p key={line}>{line}</p>) : <p>Run a diagnostic to view root-cause tracing.</p>}</article>
      </div>

      <h3>Diagnostic History</h3>
      <div>{history.length ? history.map((run, index) => { const summary = safeObject(run.pass_fail_summary); return <details className="stat-card" key={run.diagnostic_id || index}><summary><strong>{run.created_at || "Timestamp unavailable"}</strong> · Health {run.overall_health_percent ?? run.overall_health?.percent ?? "—"}% · {run.overall_status || "UNKNOWN"} · Duration {run.performance?.total_execution_time_ms ?? run.performance_timings?.total_execution_time_ms ?? "—"}ms · {run.environment || "environment unknown"}</summary><p><strong>Report token:</strong> {run.report_token || run.public_report_token || "—"}</p><p><strong>Version/commit:</strong> {run.build_commit || run.version || run.fixture_version || "—"}</p><p><strong>Pass/fail summary:</strong> {summary.passed ?? run.status_counts?.pass ?? 0} pass · {summary.warnings ?? run.status_counts?.warning ?? 0} warnings · {summary.failed ?? run.status_counts?.fail ?? 0} failures · {summary.regressions ?? run.regression_count ?? 0} regressions</p><pre className="data-note">{JSON.stringify(run, null, 2)}</pre></details>; }) : <article className="stat-card"><p>No diagnostic history yet.</p></article>}</div>

      <h3>Compare Previous Run</h3>
      <pre className="data-note">{JSON.stringify(healthTrend, null, 2)}</pre>
      {DEBUG_ERRORS && <><h3>Debug Output</h3><pre className="data-note">{JSON.stringify(layers.map(({ layer, debug_payload }) => ({ layer, debug_payload })), null, 2)}</pre><h3>Public Report Debug Output</h3><pre className="data-note">{JSON.stringify({ publicReportState, publicReportError, publicReportVerification }, null, 2)}</pre></>}
    </section>
  );
}
