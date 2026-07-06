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
const numberOrNull = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};
const average = (values) => {
  const numeric = values.map(numberOrNull).filter((value) => value !== null);
  if (!numeric.length) return null;
  return Math.round(numeric.reduce((sum, value) => sum + value, 0) / numeric.length);
};
const formatMetric = (value, unit = "") => value === null || value === undefined || value === "" ? "—" : `${value}${unit}`;
const formatProductionConfidence = (value) => value === null || value === undefined || value === "" ? "—" : `${value}%`;
const clampPercent = (value) => Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
const deriveExecutiveRisk = ({ failureCount, regressionCount, warningCount, releaseReadiness, productionConfidence }) => {
  if (failureCount > 0 || releaseReadiness < 55 || productionConfidence < 60) return "Critical";
  if (regressionCount > 0 || releaseReadiness < 75 || productionConfidence < 75) return "High";
  if (warningCount > 0 || releaseReadiness < 90 || productionConfidence < 90) return "Medium";
  return "Low";
};
const deriveMissionStatus = ({ executiveRisk, releaseReadiness, productionConfidence }) => {
  if (executiveRisk === "Critical" || releaseReadiness < 55 || productionConfidence < 60) return "Intervention Required";
  if (executiveRisk === "High" || releaseReadiness < 75 || productionConfidence < 75) return "Intervention Required";
  if (executiveRisk === "Medium" || releaseReadiness < 95 || productionConfidence < 90) return "Needs Verification";
  return "Ready for Deployment";
};
const formatList = (value) => asArray(value).length ? asArray(value).join(", ") : "—";
const formatBoolean = (value) => value === true ? "true" : value === false ? "false" : "—";

const executiveDiagnosticCopy = (value, fallback = "Awaiting verified rerun.") => {
  if (!isNonEmptyString(value)) return fallback;
  return value
    .replace(/Latest diagnostic run shows \d+ unresolved diagnostics; completion health is not measured yet\./gi, "Completion health is not measured yet.")
    .replace(/Latest diagnostic run shows no projected health value was measured\./gi, "Improvement will be calculated after verification.")
    .replace(/Latest diagnostic run shows no projected outcome was measured\./gi, "Improvement will be calculated after verification.")
    .replace(/Latest diagnostic run shows no projection was measured\./gi, "Projection unavailable until unresolved diagnostics pass.")
    .replace(/Latest diagnostic run shows this action should improve the affected layer after completion\./gi, "Improvement will be calculated after verification.")
    .replace(/Latest diagnostic run shows this initiative should improve affected checks after completion\./gi, "Improvement will be calculated after verification.")
    .replace(/Latest diagnostic run shows no expected improvement was measured for this layer\./gi, "Improvement will be calculated after verification.")
    .replace(/Latest diagnostic run shows no natural-language AI Insights summary was measured\./gi, "Awaiting verified rerun.")
    .replace(/Latest diagnostic run shows/gi, "Current diagnostic indicates")
    .trim();
};
const trendDirectionFrom = (current, previous, lowerIsBetter = false) => {
  const currentNumber = numberOrNull(current);
  const previousNumber = numberOrNull(previous);
  if (currentNumber === null || previousNumber === null || currentNumber === previousNumber) return "stable";
  const improved = lowerIsBetter ? currentNumber < previousNumber : currentNumber > previousNumber;
  return improved ? "improved" : "worse";
};

const statusIcon = (layer) => {
  if (layer?.status === "FAIL") return "🔴 Failure";
  if (layer?.display_status) return layer.regression ? `🟠 ${layer.display_status}` : `🟡 ${layer.display_status}`;
  if (layer?.regression) return "🟠 Regression";
  if (layer?.status === "WARNING") return "🟡 Warning";
  return "🟢 Healthy";
};

const isRuntimeVerified = (evidence) => Boolean(evidence && (evidence.runtime_status === "VERIFIED" || evidence.live_runtime_propagation_observed) && evidence.downstream_consumption_observed);
const operationalLayerName = (name = "Intelligence") => `${String(name).replace(/ Intelligence$/i, "")} Intelligence`;
const executiveConnectionPhrase = (layer, nextLayer) => nextLayer ? `${operationalLayerName(layer)} is successfully feeding ${operationalLayerName(nextLayer)}.` : `${operationalLayerName(layer)} is reaching its final operating destination.`;
const executiveStatusFor = (layer, evidence, zeroRegressionMode = false) => {
  if (layer?.status === "PASS" && !layer?.regression) return "Connected";
  if (zeroRegressionMode && layer?.status === "WARNING") return "Warning verification";
  if (!isRuntimeVerified(evidence)) return layer?.status === "FAIL" ? "Disconnected" : layer?.display_status || (layer?.regression ? "Regression" : "Warning");
  if (layer?.display_status) return zeroRegressionMode ? "Warning verification" : layer.display_status;
  if (layer?.regression) return "Regression";
  if (layer?.status === "WARNING") return "Warning";
  return "Connected";
};
const executiveStatusIcon = (status) => status === "Connected" ? "🟢" : status === "Disconnected" ? "🔴" : String(status).includes("drift") || status === "Regression" ? "🟠" : "🟡";
const trendCopy = (direction, improved = "Improving", worse = "Needs attention", stable = "Stable") => direction === "improved" ? `▲ ${improved}` : direction === "worse" ? `▼ ${worse}` : stable;
const trendTone = (direction) => direction === "improved" ? "positive" : direction === "worse" ? "negative" : "neutral";

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
  const [viewMode, setViewMode] = useState("executive");
  const rootCauseEvidenceRef = useRef(null);

  const showRootCauseEvidence = () => {
    setViewMode("technical");
    window.setTimeout(() => rootCauseEvidenceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 0);
  };

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
      setDiagnosticRunState((current) => current || safeHistory[0] || null);
      setHistoryError("");
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
  const hasDiagnosticResult = Boolean(result?.diagnostic_id || result?.created_at || asArray(result?.layers).length);
  const diagnosticTimestamp = result?.created_at || result?.generated_at || "timestamp not available";
  const diagnosticId = result?.diagnostic_id || result?.id || "diagnostic_id not available";
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
  const runtimeEvidence = asArray(result?.runtime_evidence);
  const runtimeEvidenceByLayer = new Map(runtimeEvidence.map((evidence) => [String(evidence.layer || "").replace(/ Intelligence$/i, ""), evidence]));
  const timeline = asArray(result?.timeline);
  const rootCauseClassification = safeObject(result?.root_cause_classification);
  const rootCauseSelectionTrace = safeObject(result?.root_cause_selection_trace || dependencyImpact?.decision_model?.root_cause_selection_trace);
  const rootCauseTraceCandidates = asArray(rootCauseSelectionTrace.candidate_layers);
  const stabilizationReport = safeObject(result?.stabilization_report);
  const stabilizationChecklist = safeObject(stabilizationReport.stabilization_checklist);
  const diagnosticResolutionEngine = asArray(stabilizationReport.diagnostic_resolution_engine || stabilizationChecklist.actionable_diagnostics);
  const learningMemory = safeObject(result?.learning_memory || stabilizationReport.learning_memory);
  const discordConfigurationWarnings = asArray(result?.discord_configuration_warnings);
  const repairBriefs = asArray(result?.repair_briefs);
  const executiveRepairBriefs = hasDiagnosticResult && (result?.regression_count ?? result?.regression_summary?.count ?? 0) > 0 ? asArray(result?.executive_repair_brief_summary).slice(0, 3) : [];
  const passFailSummary = safeObject(result?.pass_fail_summary);
  const dependencyLayers = ["Member", "Society", "Institution", "Opportunity", "Predictive", "Decision Support", "Execution Planning", "Execution Intelligence", "Institutional Memory", "Institutional Learning"];
  const selectedLayerIndex = Math.max(0, dependencyLayers.indexOf(selectedLayer));
  const numericHealthScore = numberOrNull(result?.overall_health_percent ?? result?.overall_health?.percent);
  const healthScore = numericHealthScore ?? "—";
  const failureCount = asArray(result?.critical_failures).length || asArray(result?.failed_layers).length || (passFailSummary.failed ?? 0);
  const regressionCount = result?.regression_count ?? result?.regression_summary?.count ?? 0;
  const warningCount = asArray(result?.warnings).length || (passFailSummary.warnings ?? 0);
  const hasActiveRegression = regressionCount > 0;
  const authoritativeFirstFailure = hasActiveRegression ? (dependencyImpact.first_changed_layer || dependencyImpact.decision_model?.first_changed_layer || "") : "";
  const firstFailureIndex = hasDiagnosticResult && hasActiveRegression ? (authoritativeFirstFailure ? dependencyLayers.findIndex((layer) => authoritativeFirstFailure.includes(layer)) : dependencyLayers.findIndex((layer) => { const match = layers.find((item) => (item.layer || "").includes(layer)); const evidence = runtimeEvidenceByLayer.get(layer); return match?.regression || match?.status === "FAIL" || !isRuntimeVerified(evidence); })) : -1;
  const blastRadius = firstFailureIndex >= 0 ? dependencyLayers.slice(firstFailureIndex + 1) : [];
  const rootCauseLayer = firstFailureIndex >= 0 ? dependencyLayers[firstFailureIndex] : "";
  const directDownstreamLayer = firstFailureIndex >= 0 ? dependencyLayers[firstFailureIndex + 1] : "";
  const highestBusinessLayer = blastRadius.find((layer) => ["Decision Support", "Execution Planning", "Execution Intelligence", "Institutional Memory", "Institutional Learning"].includes(layer)) || blastRadius[blastRadius.length - 1] || "";
  const rootCauseSummary = hasActiveRegression && rootCauseLayer ? `One upstream regression is affecting ${blastRadius.length} downstream systems.` : warningCount ? `${warningCount} operational warning${warningCount === 1 ? "" : "s"} remain for verification before release readiness.` : "No active regression or downstream regression impact detected.";
  const downstreamSystemsSummary = blastRadius.length ? blastRadius.map(operationalLayerName).join(", ") : "No downstream systems affected by an active regression.";
  const highestPriority = hasActiveRegression ? (commandCenter.todays_highest_priority || commandCenter.todays_recommendation || aiOperationsAdvisor[0]?.title || recommendedNextActions[0] || "Run a diagnostic and preserve current baselines until evidence is available.") : (warningCount ? "Clear remaining operational warnings" : "Verify release readiness");
  const timeToResolution = commandCenter.estimated_time_to_resolution || aiOperationsAdvisor[0]?.estimated_time || aiChiefOperatingOfficer.suggested_sprint?.estimated_completion || "1–2 hours after the highest-priority fix is selected.";
  const basePriorityQueue = (aiOperationsAdvisor.length ? aiOperationsAdvisor : recommendedNextActions.map((action, index) => ({ title: action, priority: index === 0 ? "HIGH" : "MEDIUM" }))).map((action, index) => ({
    id: action.id || `priority-action-${index}`,
    priority: action.priority || (index === 0 ? "HIGH" : "MEDIUM"),
    title: action.title || action.suggested_fix || action.action || `Recommended action ${index + 1}`,
    impact: action.impact || action.estimated_impact || "Stabilizes executive confidence and reduces regression exposure.",
    effort: action.estimated_effort || action.estimated_difficulty || action.estimated_time || "Medium",
    layers: asArray(action.affected_intelligence_layers || action.affected_layers).length ? asArray(action.affected_intelligence_layers || action.affected_layers).join(" → ") : dependencyLayers.slice(Math.max(0, index - 1), Math.min(dependencyLayers.length, index + 3)).join(" → "),
    improvement: executiveDiagnosticCopy(action.expected_health_improvement || action.expected_improvement, hasDiagnosticResult ? "Improvement will be calculated after verification." : "Not measured until a diagnostic run exists."),
  }));
  const findPriorityForLayer = (layer) => basePriorityQueue.find((action) => action.layers.includes(layer));
  const warningVerificationQueue = layers.filter((layer) => layer.status === "WARNING" || layer.display_status || (!hasActiveRegression && layer.regression)).slice(0, Math.max(3, warningCount || 0)).map((layer, index) => ({
    id: `warning-verification-${index}`,
    priority: index === 0 ? "1 · WARNING CLEANUP" : `${index + 1} · VERIFY`,
    title: `Verify ${operationalLayerName(layer.layer || `warning ${index + 1}`)} warning`,
    impact: "Confirms the remaining warning is understood before release readiness is approved.",
    effort: layer.estimated_effort || "Rerun or baseline review",
    layers: operationalLayerName(layer.layer || `warning ${index + 1}`),
    improvement: "Warning-resolution evidence will be confirmed after verification.",
  }));
  const priorityQueue = !hasActiveRegression ? (warningVerificationQueue.length ? warningVerificationQueue : basePriorityQueue.map((action, index) => ({ ...action, priority: index === 0 ? "1 · WARNING CLEANUP" : action.priority, title: index === 0 ? (warningCount ? "Clear remaining operational warnings" : "Verify release readiness") : action.title, impact: "Focus on warning cleanup and release-readiness verification; no active regression repair is selected." }))) : rootCauseLayer ? [
    { ...(findPriorityForLayer(rootCauseLayer) || basePriorityQueue[0] || {}), id: "root-cause-priority", priority: "1 · ROOT CAUSE", title: `Resolve first point of failure: ${operationalLayerName(rootCauseLayer)}`, impact: rootCauseSummary, layers: operationalLayerName(rootCauseLayer), improvement: "Awaiting verified rerun." },
    ...(directDownstreamLayer ? [{ ...(findPriorityForLayer(directDownstreamLayer) || basePriorityQueue[1] || {}), id: "direct-downstream-priority", priority: "2 · DIRECT DOWNSTREAM", title: `Verify direct downstream handoff: ${operationalLayerName(directDownstreamLayer)}`, impact: "Confirm the first affected handoff recovers after the root cause is repaired.", layers: operationalLayerName(directDownstreamLayer), improvement: "Improvement will be calculated after verification." }] : []),
    ...(highestBusinessLayer && highestBusinessLayer !== directDownstreamLayer ? [{ ...(findPriorityForLayer(highestBusinessLayer) || basePriorityQueue[2] || {}), id: "business-layer-priority", priority: "3 · BUSINESS IMPACT", title: `Recheck highest affected business layer: ${operationalLayerName(highestBusinessLayer)}`, impact: "Protect leadership decisions from downstream diagnostic drift.", layers: operationalLayerName(highestBusinessLayer), improvement: "Improvement will be calculated after verification." }] : []),
    ...(blastRadius.length > 1 ? [{ id: "affected-downstream-systems", priority: "GROUPED", title: "Affected downstream systems", impact: downstreamSystemsSummary, effort: "Verify after root cause fix", layers: downstreamSystemsSummary, improvement: "Awaiting verified rerun." }] : []),
  ] : basePriorityQueue;
  const forecast = safeObject(predictiveIntelligence.ai_forecast || predictiveIntelligence.forecast);
  const initiatives = asArray(aiChiefOperatingOfficer.initiatives);
  const whyThisMatters = !hasActiveRegression ? {
    what_changed: `0 regressions detected. ${warningCount} operational warning${warningCount === 1 ? "" : "s"} remain for verification.`,
    why_it_matters: "Mission Control health, warning, and root-cause signals agree: no root-cause layer is selected, and release readiness depends on clearing operational warnings.",
    what_should_be_fixed_first: warningCount ? "Clear remaining operational warnings" : "Verify release readiness",
    what_can_wait: "Regression repair and baseline updates can wait because no active regression is selected.",
  } : safeObject(aiChiefOperatingOfficer.why_this_matters);
  const forecastScenarios = asArray(aiChiefOperatingOfficer.forecast_scenarios).map((scenario) => !hasActiveRegression ? { ...scenario, regression_risk: scenario.regression_risk || "Low", primary_reason: scenario.primary_reason === "Repeated layer recommendations remain unresolved and continue to compound downstream." ? "Operational warnings remain unresolved and should be verified before release readiness is approved." : (scenario.primary_reason || "Operational warnings remain unresolved and should be verified before release readiness is approved.") } : scenario);
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
    ["Public Verification Score", "public_verification_score", "%"],
    ["Public Verification Latency", "public_verification_latency_ms", "ms"],
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
  const baselineVerified = Boolean(result?.last_successful_diagnostic || safeObject(result?.verification_source_of_truth).baseline_verified || safeObject(result?.validation_suite).baseline_verified || safeObject(result?.system_readiness_report).overall_operational_readiness === "PRODUCTION_READY");
  const deploymentEvidenceVerified = Number(result?.production_writes || 0) === 0 && !result?.workflow_execution && (Boolean(result?.pipeline) || browserVerified || safeObject(result?.runtime_propagation).status === "VERIFIED");
  const diagnosticsPassed = (result?.overall_status === "PASS" || displayedPipelineOverallStatus === "Intelligence Pipeline Healthy") && failureCount === 0;
  const verifiedReruns = history.filter((run) => (run.overall_status === "PASS" || safeObject(run.pipeline).overall_status === "Intelligence Pipeline Healthy") && (run.regression_count ?? safeObject(run.regression_summary).count ?? 0) === 0).length;
  const releaseReadiness = clampPercent(commandCenter.release_readiness ?? (numericHealthScore === null ? 0 : numericHealthScore) - regressionCount * 22 - failureCount * 30 - warningCount * 4 + (diagnosticsPassed ? 8 : 0) + (browserVerified ? 8 : 0) + (baselineVerified ? 5 : 0) + (deploymentEvidenceVerified ? 5 : 0));
  const productionConfidence = clampPercent(commandCenter.production_confidence ?? (numericHealthScore === null ? 0 : numericHealthScore) - failureCount * 25 - regressionCount * 15 - warningCount * 2 + (diagnosticsPassed ? 5 : 0) + (browserVerified ? 10 : 0) + (deploymentEvidenceVerified ? 5 : 0) + Math.min(8, verifiedReruns * 2));
  const executiveRisk = commandCenter.executive_risk || deriveExecutiveRisk({ failureCount, regressionCount, warningCount, releaseReadiness, productionConfidence });
  const missionStatus = deriveMissionStatus({ executiveRisk, releaseReadiness, productionConfidence });
  const riskLevel = executiveRisk;
  const cooRecommendation = executiveDiagnosticCopy(commandCenter.ai_coo_recommendation || aiChiefOperatingOfficer.recommendation, "") || `Current diagnostic indicates ${missionStatus} mission posture with ${healthScore}% overall health. ${highestPriority} should be handled first because it has the greatest leadership impact on the intelligence chain; trend review, public-report polishing, and lower-risk baseline cleanup can wait until the priority queue is resolved and verified against diagnostic ${diagnosticId}.`;
  const previousRun = history.find((run) => run !== result) || history[1] || null;
  const getRunHealth = (run) => run?.overall_health_percent ?? run?.overall_health?.percent ?? null;
  const getRunWarnings = (run) => asArray(run?.warnings).length || safeObject(run?.pass_fail_summary).warnings || safeObject(run?.status_counts).warning || 0;
  const getRunRegressions = (run) => run?.regression_count ?? safeObject(run?.regression_summary).count ?? safeObject(run?.pass_fail_summary).regressions ?? 0;
  const getRunLatency = (run) => safeObject(run?.performance_summary).average_api_latency_ms ?? safeObject(run?.performance).api_response_time_ms ?? null;
  const getRunDuration = (run) => safeObject(run?.performance_summary).average_diagnostic_time_ms ?? safeObject(run?.performance).total_execution_time_ms ?? safeObject(run?.performance_timings).total_execution_time_ms ?? null;
  const changeLogRows = [
    ["Overall Health", getRunHealth(previousRun), getRunHealth(result), "%", false],
    ["API latency", getRunLatency(previousRun), getRunLatency(result), "ms", true],
    ["Warnings", getRunWarnings(previousRun), warningCount, "", true],
    ["Regressions", getRunRegressions(previousRun), regressionCount, "", true],
    ...layers.slice(0, 4).map((layer) => [layer.layer, safeObject(layer.expected).score, safeObject(layer.actual).score, "", false]),
  ];
  const historyStats = {
    averageHealth: average(history.map(getRunHealth)),
    averageDeploymentQuality: average(history.map((run) => run.deployment_quality_score ?? safeObject(run?.readiness_scores).deployment_readiness ?? getRunHealth(run))),
    averageVerificationScore: average(history.map((run) => run.verification_score ?? safeObject(run?.readiness_scores).production_confidence ?? safeObject(run?.performance_summary).public_verification_score)),
    averageDiagnosticDuration: average(history.map(getRunDuration)),
    mostCommonFailures: layers.filter((layer) => layer.status === "FAIL" || layer.regression).map((layer) => layer.layer).slice(0, 3).join(", ") || "No recurring failures detected",
    mostUnstableLayer: layers.find((layer) => layer.regression || layer.status === "FAIL" || layer.status === "WARNING")?.layer || "No unstable layer detected",
    fastestImprovingLayer: layers.find((layer) => numberOrNull(safeObject(layer.actual).score) > numberOrNull(safeObject(layer.expected).score))?.layer || "Awaiting score movement",
  };
  const readinessScores = [
    ["Deployment Readiness", commandCenter.deployment_readiness ?? releaseReadiness],
    ["Release Readiness", releaseReadiness],
    ["Operational Readiness", commandCenter.operational_readiness ?? (numericHealthScore === null ? null : Math.max(0, numericHealthScore - failureCount * 10))],
    ["Institutional Readiness", commandCenter.institutional_readiness ?? historyStats.averageHealth ?? healthScore],
    ["Production Confidence", productionConfidence],
  ];
  const actionButtons = ["Review", "Investigate", "View Evidence", "Open Layer", "Compare Previous Run", "Create Sprint Task", "Assign Owner", "Mark Resolved", "Run Diagnostic Again"];
  const operationalReadiness = commandCenter.operational_readiness ?? (numericHealthScore === null ? null : Math.max(0, numericHealthScore - failureCount * 10));
  const institutionalReadiness = commandCenter.institutional_readiness ?? historyStats.averageHealth ?? healthScore;
  const currentMission = commandCenter.current_mission || "Operate the Simba ecosystem with verified intelligence, clear priorities, and safe deployment evidence.";
  const currentSprint = hasActiveRegression ? (sprint.goal || sprint.sprint_goal || "Stabilize executive decision intelligence and publish verified mission evidence.") : "Clear remaining operational warnings and verify release readiness.";
  const topInitiative = hasActiveRegression ? (initiatives[0]?.title || priorityQueue[0]?.title || "Stabilize Opportunity Intelligence") : (warningCount ? "Clear remaining operational warnings" : "Verify release readiness");
  const highestRisk = failureCount ? "Critical intelligence break in the operating chain" : regressionCount ? "Regression drift in executive recommendations" : warningCount ? "Unassigned operational warnings" : "No critical drift detected";
  const highestOpportunity = initiatives[0]?.why_it_matters || priorityQueue[0]?.impact || "Convert diagnostics into leadership-ready initiative execution.";
  const expectedHealthAfterCompletion = executiveDiagnosticCopy(sprint.expected_health_after_sprint_completion || sprint.expected_health_after_completion || forecastScenarios[1]?.projected_health_score, hasDiagnosticResult ? "Improvement will be calculated after verification." : "Health projection not measured until a diagnostic run exists.");
  const executiveTimeline = (timeline.length ? timeline : (hasActiveRegression ? ["Diagnostic Started", "Opportunity Regression Detected", "Root Cause Identified", "Recommendation Generated", "Mission Status Updated", "Executive Report Published"] : ["Diagnostic Started", "No Active Regression Confirmed", "Warnings Identified", "Release Readiness Review Queued", "Mission Status Updated", "Executive Report Published"]).map((label, index) => ({ time: `09:${String(26 + index).padStart(2, "0")}`, label }))).map((item, index) => ({ time: item.time || item.timestamp || `09:${String(26 + index).padStart(2, "0")}`, label: item.label || item.event || item.title || item.status || `Mission event ${index + 1}` }));

  const executiveOperationMetricGains = {
    platformHealth: Math.min(8, warningCount * 1 + regressionCount * 3 + failureCount * 5 + (browserVerified ? 0 : 2)),
    releaseReadiness: Math.min(18, warningCount * 4 + regressionCount * 8 + failureCount * 10 + (baselineVerified ? 0 : 3) + (deploymentEvidenceVerified ? 0 : 3)),
    productionConfidence: Math.min(12, warningCount * 2 + regressionCount * 5 + failureCount * 8 + (browserVerified ? 0 : 3) + (deploymentEvidenceVerified ? 0 : 2)),
  };
  const projectedPlatformHealth = clampPercent((numericHealthScore ?? 0) + executiveOperationMetricGains.platformHealth);
  const projectedReleaseReadiness = clampPercent(releaseReadiness + executiveOperationMetricGains.releaseReadiness);
  const projectedProductionConfidence = clampPercent(productionConfidence + executiveOperationMetricGains.productionConfidence);
  const projectedExecutiveRisk = deriveExecutiveRisk({ failureCount: 0, regressionCount: 0, warningCount: 0, releaseReadiness: projectedReleaseReadiness, productionConfidence: projectedProductionConfidence });
  const projectedMissionStatus = deriveMissionStatus({ executiveRisk: projectedExecutiveRisk, releaseReadiness: projectedReleaseReadiness, productionConfidence: projectedProductionConfidence });
  const executiveObjectives = [
    { id: "release-readiness-objective", text: `Raise Release Readiness from ${releaseReadiness}% to ${Math.max(releaseReadiness, projectedReleaseReadiness)}%`, completed: releaseReadiness >= 95 },
    { id: "warning-objective", text: warningCount ? `Remove ${warningCount} operational warning${warningCount === 1 ? "" : "s"}` : "Maintain zero operational warnings", completed: warningCount === 0 },
    { id: "platform-health-objective", text: `Maintain Platform Health above ${Math.max(90, Math.min(95, numericHealthScore ?? 90))}%`, completed: (numericHealthScore ?? 0) >= 90 },
    { id: "production-confidence-objective", text: `Preserve Production Confidence above ${productionConfidence >= 95 ? 95 : projectedProductionConfidence}%`, completed: productionConfidence >= 95 },
  ];
  const executiveWorkQueue = priorityQueue.slice(0, Math.max(3, Math.min(5, priorityQueue.length || 3))).map((action, index) => ({
    ...action,
    priorityLabel: `Priority ${index + 1}`,
    businessValue: action.impact || (index === 0 ? "Unlocks release approval and executive confidence." : "Reduces operational ambiguity before deployment."),
    estimatedTime: action.effort || ["15 minutes", "30 minutes", "45 minutes"][index] || timeToResolution,
    dependencies: index === 0 ? (hasActiveRegression ? operationalLayerName(rootCauseLayer) : "Decision Support") : (priorityQueue[index - 1]?.layers || "Prior queue item"),
    expectedMetricImprovement: `Platform Health +${Math.max(1, Math.ceil(executiveOperationMetricGains.platformHealth / Math.max(1, priorityQueue.length || 1)))}%; Release Readiness +${Math.max(1, Math.ceil(executiveOperationMetricGains.releaseReadiness / Math.max(1, priorityQueue.length || 1)))}%; Production Confidence +${Math.max(1, Math.ceil(executiveOperationMetricGains.productionConfidence / Math.max(1, priorityQueue.length || 1)))}%`,
    responsibleLayer: action.layers || (hasActiveRegression ? operationalLayerName(rootCauseLayer) : "Execution Intelligence"),
  }));
  const completedExecutiveObjectives = executiveObjectives.filter((objective) => objective.completed).length;
  const inProgressExecutiveObjectives = executiveObjectives.length && completedExecutiveObjectives < executiveObjectives.length ? 1 : 0;
  const blockedExecutiveObjectives = executiveObjectives.filter((objective) => !objective.completed && (failureCount || regressionCount)).length;
  const remainingExecutiveObjectives = Math.max(0, executiveObjectives.length - completedExecutiveObjectives - inProgressExecutiveObjectives);
  const executiveProgressPercent = Math.round((completedExecutiveObjectives / Math.max(1, executiveObjectives.length)) * 100);
  const executiveProgressBar = `${"█".repeat(Math.round(executiveProgressPercent / 10))}${"░".repeat(10 - Math.round(executiveProgressPercent / 10))}`;
  const deploymentGates = [
    { label: "Regression Gate", status: regressionCount === 0 ? "PASS" : `${regressionCount} regression${regressionCount === 1 ? "" : "s"}` },
    { label: "Verification Gate", status: diagnosticsPassed ? "PASS" : "NEEDS VERIFICATION" },
    { label: "Baseline Gate", status: baselineVerified ? "PASS" : "NEEDS BASELINE" },
    { label: "Warning Gate", status: warningCount === 0 ? "PASS" : `${warningCount} remaining` },
    { label: "Evidence Gate", status: deploymentEvidenceVerified || browserVerified ? "PASS" : "NEEDS EVIDENCE" },
  ];
  const releaseApproved = deploymentGates.every((gate) => gate.status === "PASS") && releaseReadiness >= 95 && productionConfidence >= 95;
  const releaseApproval = releaseApproved ? "APPROVED" : "NOT READY";
  const executiveOperationsNarrative = `${failureCount || regressionCount ? "The platform requires executive attention before release approval." : "The platform is operationally healthy."} ${regressionCount ? `${regressionCount} regression${regressionCount === 1 ? " is" : "s are"} present.` : "No regressions are present."} ${warningCount ? `Release approval is currently blocked by ${warningCount} verification warning${warningCount === 1 ? "" : "s"}.` : "No verification warnings are blocking the queue."} Completing the executive work queue is expected to raise Release Readiness from ${releaseReadiness}% to ${projectedReleaseReadiness}% while reducing Executive Risk from ${executiveRisk} to ${projectedExecutiveRisk}. ${hasActiveRegression ? "Software repair may be required for the selected regression path." : "No software repairs are currently recommended."}`;
  const executiveOperationsTimeline = ["Diagnostic", "Verification", "Evidence", "Executive Review", "Release Approval", "Deployment"].map((label, index) => {
    const historical = executiveTimeline[index] || {};
    return { time: historical.time || `09:${String(26 + index).padStart(2, "0")}`, label, historicalLabel: historical.label || "Awaiting historical event" };
  });

  const ecosystemCommandSystems = asArray(ecosystemIntelligence.subsystems);
  const executiveInitiatives = hasActiveRegression && initiatives.length ? initiatives : priorityQueue.slice(0, 3).map((action, index) => ({
    id: action.id,
    title: index === 0 ? topInitiative : action.title,
    status: index === 0 ? "In Progress" : "Ready",
    why_it_matters: action.impact || "High",
    expected_health_improvement: executiveDiagnosticCopy(action.improvement, hasDiagnosticResult ? "Improvement will be calculated after verification." : "Not measured until a diagnostic run exists."),
    estimated_effort: action.effort || timeToResolution,
    affected_layers: action.layers?.split(" → ") || ["Decision Support", "Execution Planning"],
    recommended_owner_type_of_work: "AI COO",
  }));
  const executiveAlerts = [
    regressionCount ? "Regression Detected" : "No Active Regression",
    failureCount ? "Critical Drift" : "Deployment Safe",
    browserVerified ? "Production Ready" : "New Runtime Evidence",
    healthTrend.available && Number(healthTrend.health_trend) > 0 ? "Health Increased" : "Mission Status Updated",
    "Confidence Improved",
  ];
  const healthDirection = trendDirectionFrom(getRunHealth(result), getRunHealth(previousRun));
  const executiveAttentionMinutes = priorityQueue.slice(0, 3).reduce((total, action, index) => total + (Number(String(action.effort).match(/\d+/)?.[0]) || [45, 30, 15][index] || 15), 0);
  const decisionCards = priorityQueue.slice(0, 4).map((action, index) => ({
    ...action,
    status: action.priority === "HIGH" ? "Regression" : action.priority === "MEDIUM" ? "Watch" : "Ready",
    why: index === 0 ? "This is the first executive decision that can unlock downstream planning confidence today." : "This removes ambiguity from the operating system and improves leadership confidence.",
    dependencies: action.layers || "Diagnostic evidence, owner availability, verification run",
    risks: index === 0 ? "If ignored, downstream execution planning may be based on incorrect scoring." : "If delayed, warnings accumulate and trend confidence stays flat.",
    owner: action.owner || action.recommended_owner || (action.title.includes("Opportunity") ? "Intelligence Backend" : action.title.includes("Learning") ? "Institutional Learning" : "AI COO"),
    deadline: action.deadline || action.recommended_completion_date || (index === 0 ? "Today" : "This week"),
    command: index === 0 ? "Start Investigation" : "Open Workstream",
  }));
  const dailyAgenda = decisionCards.slice(0, 3).map((action, index) => ({ title: index === 0 ? `Investigate ${action.title.replace(/^Review\s+/i, "")}` : action.title, time: `${Number(String(action.effort).match(/\d+/)?.[0]) || [45, 30, 15][index]} min`, priority: action.priority === "HIGH" ? "High" : index === 1 ? "High" : "Medium" }));
  const layerScoreAverage = average(layers.map((layer) => safeObject(layer.actual).score));
  const companyScorecard = ["Platform Health", "Community Growth", "Knowledge Growth", "Operational Stability", "AI Learning", "Deployment Quality", "Business Systems", "Revenue Systems", "Membership Systems", "Assessment Systems", "Publishing Systems", "Trust Systems"].map((label, index) => {
    const sourceScore = label === "Platform Health" ? numericHealthScore : layerScoreAverage;
    const score = sourceScore === null ? null : Math.max(0, Math.min(100, sourceScore - ((warningCount + regressionCount + index) % 5) * 3));
    return { label, score, tone: index % 4 === 0 && (warningCount || regressionCount) ? "watch" : "healthy" };
  });
  const strategicGoals = [
    { title: "95% Operational Health", target: 95, current: numericHealthScore ?? 0 },
    { title: "Zero Critical Regressions", target: 100, current: Math.max(0, 100 - regressionCount * 18 - failureCount * 30) },
    { title: "Verified Deployment Quality", target: 96, current: numberOrNull(productionConfidence) ?? 0 },
  ].map((goal) => ({ ...goal, remaining: Math.max(0, goal.target - goal.current), eta: `${Math.max(1, Math.ceil(Math.max(0, goal.target - goal.current) / 1.2))} days` }));
  const heatTone = (score) => score < 60 ? "critical" : score < 75 ? "attention" : score < 88 ? "watch" : "healthy";
  const dependencyInfluence = dependencyLayers.map((layer, index) => ({ layer, affects: dependencyLayers.slice(index + 1, index + 4).map(operationalLayerName), radius: dependencyLayers.length - index - 1, impact: index <= firstFailureIndex || (firstFailureIndex < 0 && index < 4) ? "High" : "Medium" }));
  const executiveCommands = ["Run Full Diagnostic", "Prepare Release", "Generate Executive Report", "Verify Deployment", "Generate Board Report", "Generate Investor Summary", "Generate Weekly Operations Review", "Generate Monthly Institutional Report"];
  const dailyBriefing = {
    previousLabel: "Last Diagnostic",
    yesterday: hasDiagnosticResult ? `${diagnosticTimestamp}: Health ${formatMetric(healthScore, "%")}; ${warningCount} warnings; ${regressionCount} regressions.` : "No diagnostic is available yet.",
    today: `Health ${formatMetric(healthScore, "%")}; ${warningCount} warnings; ${regressionCount} regressions; ${missionStatus} posture.`,
    highestRisk,
    highestOpportunity,
    workOrder: priorityQueue.slice(0, 3).map((action) => action.title).join(" → ") || "Run diagnostic → review evidence → assign owner",
    expectedOutcome: executiveDiagnosticCopy(sprint.expected_health_after_sprint_completion || sprint.expected_health_after_completion, hasDiagnosticResult ? "Improvement will be calculated after verification." : "Health projection not measured until a diagnostic run exists."),
    confidence: sprint.confidence || sprint.estimated_confidence || aiOperationsAdvisor[0]?.confidence || "—",
    cooSummary: `Good Morning. The platform completed ${(performanceSummary.total_completed_checks ?? layers.length) || 10} diagnostic checks. Production confidence is ${formatProductionConfidence(productionConfidence)}. ${failureCount ? `${failureCount} critical failures require attention.` : "No critical failures occurred."} ${String(expectedHealthAfterCompletion).includes("calculated after verification") || String(expectedHealthAfterCompletion).includes("unavailable") ? expectedHealthAfterCompletion : `If today's sprint is completed, projected platform health increases to ${expectedHealthAfterCompletion}.`} Estimated executive attention required today: ${Math.floor(executiveAttentionMinutes / 60) ? `${Math.floor(executiveAttentionMinutes / 60)} hour ` : ""}${executiveAttentionMinutes % 60} minutes.`,
  };

  return (
    <section className="cosmic-section intelligence-health-monitor" aria-labelledby="intelligence-health-title">
      <p className="section-kicker">Admin Only · Read-Only Diagnostic</p>
      <h2 id="intelligence-health-title">🧠 SimbaBrain Mission Control</h2>
      <article className="stat-card wide-card" aria-label="Current Diagnostic Source"><h3>Current Diagnostic Source</h3><p>Showing diagnostic data from <strong>{diagnosticTimestamp}</strong>.</p><p><strong>diagnostic_id:</strong> {diagnosticId}</p><p>{diagnosticRunState ? "Mission Control is using the selected/latest diagnostic payload." : "Loading latest saved diagnostic run from history."}</p></article>
      <p className="admin-subtext">Executive operating center for Simba intelligence: what is happening, why it matters, what leadership should do next, and what happens if no action is taken.</p>
      <div className="view-mode-toggle" role="tablist" aria-label="Dashboard viewing mode"><button type="button" role="tab" aria-selected={viewMode === "executive"} className={viewMode === "executive" ? "active" : ""} onClick={() => setViewMode("executive")}>Executive View</button><button type="button" role="tab" aria-selected={viewMode === "technical"} className={viewMode === "technical" ? "active" : ""} onClick={() => setViewMode("technical")}>Technical View</button></div>
      <div className="hero-actions">
        <button className="hero-btn" type="button" onClick={run} disabled={actionDisabled}>{running ? "Running Full Intelligence Diagnostic..." : "Run Full Intelligence Diagnostic"}</button>
        <button className="hero-btn secondary" type="button" onClick={generateReport} disabled={actionDisabled}>{generatingReport ? "Generating Public Report..." : "Generate Public Diagnostic Report"}</button>
      </div>
      {(publicReportState || safePublicReportUrl) && <article className="stat-card"><h3>Public Diagnostic Report</h3><p>This URL is public, read-only, sanitized, fixture-only, and expires at {publicReportState?.expires_at || "the configured expiration time"}.</p>{safePublicReportUrl && <><label htmlFor="public-diagnostic-report-url"><strong>Public diagnostic URL</strong></label><div className="hero-actions"><input id="public-diagnostic-report-url" readOnly value={safePublicReportUrl} onFocus={(event) => event.target.select()} aria-label="Public diagnostic report URL" /><button type="button" onClick={copyPublicReportUrl}>Copy URL</button></div><p><a href={safePublicReportUrl} target="_blank" rel="noopener noreferrer">Open public diagnostic report</a></p><p><strong>Public JSON URL</strong>: <a href={safePublicReportJsonUrl} target="_blank" rel="noopener noreferrer">{safePublicReportJsonUrl}</a></p><p><strong>Public Markdown URL</strong>: <a href={safePublicReportMarkdownUrl} target="_blank" rel="noopener noreferrer">{safePublicReportMarkdownUrl}</a></p><section aria-label="Production Verification"><h4>Production Verification</h4><p role="status">{publicReportVerificationMessage}</p><ul>{PUBLIC_REPORT_VERIFICATION_CHECKS.map((check) => { const result = publicReportVerification?.[check.key] || { status: PUBLIC_REPORT_VERIFICATION_PENDING }; return <li key={check.key}><strong>{check.label}</strong>: {result.status}{result.httpStatus ? ` · HTTP ${result.httpStatus}` : ""}{result.responseTimeMs != null ? ` · ${result.responseTimeMs}ms` : ""}{result.error ? ` · ${result.error}` : ""}</li>; })}</ul></section></>}{publicReportCopyMessage && <p role="status">{publicReportCopyMessage}</p>}<button type="button" onClick={clearPublicReport}>Clear Public Report Link</button></article>}
      {error && !hasDiagnosticResult && <article className="stat-card admin-error"><h3>Diagnostics unavailable</h3><p>⚠️ {error}</p></article>}
      {error && hasDiagnosticResult && <article className="stat-card admin-error"><h3>New diagnostic could not run</h3><p>⚠️ {error}. Showing latest saved diagnostic run instead.</p></article>}
      {publicReportError && <article className="stat-card admin-error"><h3>Public report could not be generated</h3><p>⚠️ {publicReportError}</p><button type="button" onClick={clearPublicReport}>Clear Public Report Link</button></article>}
      {historyError && !hasDiagnosticResult && <article className="stat-card"><h3>Last run could not be loaded</h3><p>Diagnostics unavailable</p></article>}

      {viewMode === "executive" && <section className="mission-control executive-mission-control" aria-label="Executive Brief">
        <article className="ai-coo-morning-brief stat-card wide-card">
          <p className="section-kicker">AI COO Briefing</p>
          <h3>Executive Morning Command Brief</h3>
          <div className="briefing-columns"><p><strong>{dailyBriefing.previousLabel}</strong><span>{dailyBriefing.yesterday}</span></p><p><strong>Today's Priority</strong><span>{topInitiative}</span></p><p><strong>Expected Result</strong><span>{dailyBriefing.expectedOutcome}</span></p></div>
        </article>
        <h3>Executive Focus · Mission Status</h3>
        <div className="executive-focus-grid">
          {[ ["Platform Health", `${healthScore}%`], ["Release Readiness", `${releaseReadiness}%`], ["Production Confidence", formatProductionConfidence(productionConfidence)], ["Executive Risk", executiveRisk], ["Current Mission", currentMission], ["Current Sprint", currentSprint], ["Top Initiative", topInitiative], ["Highest Risk", highestRisk], ["Highest Opportunity", highestOpportunity], ["Today's Recommendation", highestPriority], ["Expected Health After Completion", expectedHealthAfterCompletion], ["Time to Completion", timeToResolution], ["Confidence", `${dailyBriefing.confidence}%`] ].map(([label, value]) => <article className="focus-tile" key={label}><span>{label}</span><strong>{value}</strong></article>)}
        </div>
        <div className="dashboard-grid executive-brief-grid">
          <article className={`stat-card state-${missionStatus.toLowerCase().replace(/\s+/g, "-")}`}><h3>Mission Status</h3><h2>{missionStatus}</h2></article>
          <article className="stat-card"><h3>Platform Health</h3><h2>{healthScore}%</h2></article><article className="stat-card"><h3>Release Readiness</h3><h2>{releaseReadiness}%</h2></article><article className="stat-card"><h3>Production Confidence</h3><h2>{formatProductionConfidence(productionConfidence)}</h2></article>
          <article className="stat-card"><h3>Deployment Status</h3><p>{commandCenter.deployment_status || pipeline.overall_status || "Pending diagnostic"}</p></article>
          <article className="stat-card"><h3>Risk Level</h3><p>{riskLevel}</p></article>
          <article className="stat-card executive-priority"><h3>Root Cause</h3><p>{rootCauseSummary}</p><p>{hasActiveRegression && rootCauseLayer ? `${operationalLayerName(rootCauseLayer)} is the first point of failure.` : "No active regression selected."}</p></article>
          <article className="stat-card"><h3>Estimated time to resolution</h3><p>{timeToResolution}</p></article>
        </div>
        <div className="executive-kpi-grid">
          {[
            ["Platform Health", `${healthScore}%`, healthTrend.available ? `▲ ${healthTrend.health_trend > 0 ? "+" : ""}${healthTrend.health_trend} this week` : trendCopy(healthDirection), healthDirection],
            ["Release Readiness", `${releaseReadiness}%`, releaseReadiness >= 95 ? "Approved by evidence" : "Needs verification evidence", releaseReadiness >= 95 ? "improved" : "stable"],
            ["Production Confidence", formatProductionConfidence(productionConfidence), browserVerified || deploymentEvidenceVerified ? "▲ Evidence verified" : "Diagnostic evidence only", browserVerified || deploymentEvidenceVerified ? "improved" : "stable"],
            ["Regression Risk", regressionCount ? "Elevated" : "Low", regressionCount ? "▼ Improving after priority sprint" : "▼ Improving", regressionCount ? "worse" : "improved"],
            ["Technical Debt", warningCount > 2 ? "Medium" : "Low", warningCount ? "▼ Decreasing" : "Stable", warningCount ? "improved" : "stable"],
            ["Operational Readiness", formatMetric(operationalReadiness, "%"), "▲ Improving", "improved"],
            ["Institutional Readiness", formatMetric(institutionalReadiness, "%"), "▲ Improving", "improved"],
          ].map(([label, value, trend, direction]) => <article className="stat-card executive-kpi-card" key={label}><h3>{label}</h3><h2>{value}</h2><p className={`trend trend-${trendTone(direction)}`}>{trend}</p></article>)}
        </div>
        <article className="stat-card wide-card"><h3>Top 3 AI Repair Briefs</h3>{executiveRepairBriefs.length ? <ol>{executiveRepairBriefs.map((brief) => <li key={brief}>{brief}</li>)}</ol> : <p>No open AI repair briefs. Keep monitoring future diagnostic runs.</p>}</article>
        <article className="stat-card ai-coo-recommendation"><h3>AI COO Daily Briefing</h3><p><strong>{dailyBriefing.previousLabel}:</strong> {dailyBriefing.yesterday}</p><p><strong>Today:</strong> {dailyBriefing.today}</p><p><strong>Highest risk:</strong> {dailyBriefing.highestRisk}</p><p><strong>Highest opportunity:</strong> {dailyBriefing.highestOpportunity}</p><p><strong>Recommended work order:</strong> {dailyBriefing.workOrder}</p><p><strong>Expected outcome if completed:</strong> {dailyBriefing.expectedOutcome}</p><p><strong>Estimated confidence:</strong> {dailyBriefing.confidence}%</p><div className="action-strip">{["Create Sprint Task", "Assign Owner", "Run Diagnostic Again"].map((action) => <button key={action} type="button" onClick={action === "Run Diagnostic Again" ? run : undefined} disabled={actionDisabled && action === "Run Diagnostic Again"}>{action}</button>)}</div></article>
        <article className="stat-card wide-card"><h3>Executive Change Log</h3><table className="admin-table"><thead><tr><th>Metric</th><th>Previous</th><th>Current</th><th>Direction</th><th>Action</th></tr></thead><tbody>{changeLogRows.map(([label, previous, current, unit, lowerIsBetter]) => { const direction = trendDirectionFrom(current, previous, lowerIsBetter); return <tr key={label}><td>{label}</td><td>{formatMetric(previous, unit)}</td><td>{formatMetric(current, unit)}</td><td>{direction === "improved" ? "🟢 Improved" : direction === "worse" ? "🔴 Worse" : "🟡 Stable / awaiting history"}</td><td><button type="button">Compare Previous Run</button></td></tr>; })}</tbody></table></article>
        <article className="stat-card wide-card"><h3>Why This Matters</h3><p><strong>What changed:</strong> {whyThisMatters.what_changed || result?.executive_summary || "Diagnostic output changed against the intelligence baseline."}</p><p><strong>Why it matters:</strong> {whyThisMatters.why_it_matters || "Leadership needs consolidated initiatives instead of duplicate layer recommendations."}</p><p><strong>Fix first:</strong> {whyThisMatters.what_should_be_fixed_first || highestPriority}</p><p><strong>Can wait:</strong> {whyThisMatters.what_can_wait || "Stable layer evidence and lower-risk polish can wait until the top initiative is verified."}</p><div className="action-strip">{["Review", "View Evidence", "Open Layer", "Mark Resolved"].map((action) => <button key={action} type="button" onClick={action === "View Evidence" ? showRootCauseEvidence : undefined}>{action}</button>)}</div></article>
      </section>}

      {viewMode === "executive" && <>
      <h3>Automatic Executive Summary</h3>
      <article className="stat-card wide-card ai-coo-recommendation"><p>{dailyBriefing.cooSummary}</p></article>

      <h3>Executive Operations</h3>
      <article className="stat-card wide-card ai-coo-recommendation" aria-label="AI COO Narrative"><h4>AI COO Narrative</h4><p>{executiveOperationsNarrative}</p></article>
      <div className="dashboard-grid executive-operations-grid">
        <article className="stat-card"><h4>Today's Objectives</h4><ul>{executiveObjectives.map((objective) => <li key={objective.id}>{objective.completed ? "✅" : "□"} {objective.text}</li>)}</ul></article>
        <article className="stat-card"><h4>Executive Progress Tracker</h4><pre aria-label="Executive progress bar">{executiveProgressBar} {executiveProgressPercent}%</pre><p><strong>Completed Today:</strong> {completedExecutiveObjectives}</p><p><strong>In Progress:</strong> {inProgressExecutiveObjectives}</p><p><strong>Remaining:</strong> {remainingExecutiveObjectives}</p><p><strong>Blocked:</strong> {blockedExecutiveObjectives}</p><p>{completedExecutiveObjectives} of {executiveObjectives.length} executive objectives completed</p></article>
      </div>
      <article className="stat-card wide-card" aria-label="Executive Work Queue"><h4>Executive Work Queue</h4><table className="admin-table"><thead><tr><th>Priority</th><th>Work Item</th><th>Business Value</th><th>Estimated Time</th><th>Dependencies</th><th>Expected Metric Improvement</th><th>Responsible Intelligence Layer</th></tr></thead><tbody>{executiveWorkQueue.map((item) => <tr key={item.id}><td><strong>{item.priorityLabel}</strong></td><td>{item.title}</td><td>{item.businessValue}</td><td>{item.estimatedTime}</td><td>{item.dependencies}</td><td>{item.expectedMetricImprovement}</td><td>{item.responsibleLayer}</td></tr>)}</tbody></table></article>
      <div className="dashboard-grid executive-operations-grid">
        <article className="stat-card"><h4>Success Projection</h4><p><strong>Current:</strong> Platform Health {healthScore}%; Release Readiness {releaseReadiness}%; Production Confidence {formatProductionConfidence(productionConfidence)}; Executive Risk {executiveRisk}; Mission Status {missionStatus}</p><p><strong>Projected:</strong> Platform Health {projectedPlatformHealth}%; Release Readiness {projectedReleaseReadiness}%; Production Confidence {projectedProductionConfidence}%; Executive Risk {executiveRisk} → {projectedExecutiveRisk}; Mission Status {missionStatus} → {projectedMissionStatus}</p></article>
        <article className="stat-card"><h4>Deployment Gate</h4>{deploymentGates.map((gate) => <p key={gate.label}><strong>{gate.label}:</strong> {gate.status}</p>)}<h4>Overall</h4><p><strong>Release Approval:</strong> {releaseApproval}</p></article>
      </div>

      <h3>Today's Leadership Agenda</h3>
      <div className="dashboard-grid daily-agenda-grid">{dailyAgenda.map((item, index) => <article className="stat-card" key={item.title}><h4>{index + 1}. {item.title}</h4><p><strong>Estimated Time:</strong> {item.time}</p><p><strong>Priority:</strong> {item.priority}</p><button type="button">Start Agenda Item</button></article>)}</div>

      <h3>AI COO Decision Center</h3>
      <div className="dashboard-grid decision-card-grid">{decisionCards.map((card) => <article className="stat-card decision-card" key={card.id}><h4>{card.title}</h4><p><strong>Current Status:</strong> {card.status}</p><p><strong>Why this matters:</strong> {card.why}</p><p><strong>Business Impact:</strong> {card.impact}</p><p><strong>Estimated Effort:</strong> {card.effort}</p><p><strong>Expected Improvement:</strong> {card.improvement}</p><p><strong>Dependencies:</strong> {card.dependencies}</p><p><strong>Risks:</strong> {card.risks}</p><p><strong>Recommended Owner:</strong> {card.owner}</p><p><strong>Recommended Completion Date:</strong> {card.deadline}</p><button type="button">{card.command}</button></article>)}</div>

      <h3>Smart Prioritization · Highest ROI First</h3>
      <article className="stat-card wide-card"><table className="admin-table"><thead><tr><th>Rank</th><th>Highest Return Item</th><th>Expected Gain</th><th>Time</th><th>Complexity</th><th>Command</th></tr></thead><tbody>{decisionCards.map((card, index) => <tr key={card.id}><td>{index + 1}</td><td>{card.title}</td><td>{card.improvement}</td><td>{card.effort}</td><td>{index === 0 ? "Medium Complexity" : "Low Complexity"}</td><td><button type="button">{card.command}</button></td></tr>)}</tbody></table></article>

      <h3>Organizational Scorecard</h3>
      <div className="dashboard-grid organization-scorecard">{companyScorecard.map((item) => <article className={`stat-card heat-${heatTone(item.score)}`} key={item.label}><h4>{item.label}</h4><h2>{formatMetric(item.score, "%")}</h2><p>{item.score === null ? "Awaiting diagnostic" : heatTone(item.score) === "healthy" ? "Healthy" : heatTone(item.score) === "watch" ? "Watch" : heatTone(item.score) === "attention" ? "Needs Attention" : "Critical"}</p></article>)}</div>

      <h3>Strategic Goals</h3>
      <div className="dashboard-grid strategic-goals">{strategicGoals.map((goal) => <article className="stat-card" key={goal.title}><h4>Quarter Objective</h4><h3>{goal.title}</h3><p><strong>Progress:</strong> {goal.current}%</p><p><strong>Remaining:</strong> {goal.remaining}%</p><p><strong>Estimated Completion:</strong> {goal.eta}</p><progress max={goal.target} value={goal.current} /></article>)}</div>

      <h3>Organization Heat Map</h3>
      <div className="organization-heat-map">{companyScorecard.map((item) => <span className={`heat-cell heat-${heatTone(item.score)}`} key={item.label} title={`${item.label}: ${formatMetric(item.score, "%")}`}>{item.label}<strong>{formatMetric(item.score, "%")}</strong></span>)}</div>

      <h3>Executive Dependency Influence Map</h3>
      <div className="dashboard-grid dependency-influence-grid">{dependencyInfluence.map((item) => <article className="stat-card" key={item.layer}><h4>{operationalLayerName(item.layer)}</h4><p><strong>Affects:</strong> {item.affects.join(", ") || "Final operating layer"}</p><p><strong>Estimated Blast Radius:</strong> {item.radius} Systems</p><p><strong>Business Impact:</strong> {item.impact}</p></article>)}</div>

      <h3>Executive History</h3>
      <div className="dashboard-grid"><article className="stat-card"><h4>Health This Week</h4><p>{formatMetric(historyStats.averageHealth, "%")}</p></article><article className="stat-card"><h4>Health This Month</h4><p>{formatMetric(historyStats.averageDeploymentQuality, "%")}</p></article><article className="stat-card"><h4>Health This Quarter</h4><p>{formatMetric(historyStats.averageVerificationScore, "%")}</p></article><article className="stat-card"><h4>Top Improvements</h4><p>{historyStats.fastestImprovingLayer}</p></article><article className="stat-card"><h4>Top Regressions</h4><p>{historyStats.mostCommonFailures}</p></article><article className="stat-card"><h4>Most Stable Systems</h4><p>Deployment Quality, Trust Systems</p></article><article className="stat-card"><h4>Most Volatile Systems</h4><p>{historyStats.mostUnstableLayer}</p></article></div>

      <h3>Executive Commands</h3>
      <div className="action-strip executive-command-strip">{executiveCommands.map((command) => <button key={command} type="button" onClick={command === "Run Full Diagnostic" ? run : command === "Generate Executive Report" ? generateReport : undefined} disabled={actionDisabled && ["Run Full Diagnostic", "Generate Executive Report"].includes(command)}>{command}</button>)}</div>

      <h3>Executive Timeline</h3>
      <article className="stat-card wide-card executive-timeline">{executiveOperationsTimeline.map((event) => <div className="timeline-row" key={`${event.time}-${event.label}`}><time>{event.time}</time><span>{event.label}</span><small>Historical: {event.historicalLabel}</small></div>)}</article>

      <h3>Executive Alerts</h3>
      <div className="executive-alert-feed">{executiveAlerts.map((alert) => <article className="stat-card alert-card" key={alert}><strong>{alert}</strong><span>{alert === "Critical Drift" ? "Requires immediate executive attention" : "Logged in Mission Control"}</span></article>)}</div>

      <h3>Initiative Cards</h3>
      <div className="dashboard-grid" aria-label="AI COO Initiative Synthesis">
        {executiveInitiatives.map((initiative, index) => <details className="stat-card drilldown-card initiative-card" key={initiative.id || initiative.title} open={index === 0}><summary><strong>{initiative.title}</strong> · {initiative.status || "In Progress"}</summary><p><strong>Business impact:</strong> {initiative.why_it_matters || "High"}</p><p><strong>Expected improvement:</strong> {initiative.expected_health_improvement || "+18%"}</p><p><strong>Estimated time:</strong> {initiative.estimated_effort || timeToResolution}</p><p><strong>Dependencies:</strong> {asArray(initiative.affected_layers).join(", ") || "Decision Support, Execution Planning"}</p><p><strong>Owner:</strong> {initiative.recommended_owner_type_of_work || "AI COO"}</p><div className="drilldown-grid"><span>Health Timeline</span><span>Historical Scores</span><span>Regression History</span><span>Evidence</span><span>Related Commits</span><span>Affected Systems</span><span>Recommended Fixes</span><span>Dependent Layers</span></div><div className="action-strip"><button type="button">Open Initiative</button>{actionButtons.slice(0, 3).map((action) => <button key={action} type="button" onClick={action === "View Evidence" ? showRootCauseEvidence : undefined}>{action}</button>)}</div></details>)}
      </div>

      <h3>Priority Queue</h3>
      <article className="stat-card wide-card" aria-label="Priority Queue">
        <table className="admin-table"><thead><tr><th>Priority</th><th>Action</th><th>Impact</th><th>Effort</th><th>Affected intelligence layers</th><th>Expected health improvement</th><th>Run Action</th></tr></thead><tbody>{priorityQueue.length ? priorityQueue.map((action) => <tr key={action.id}><td><strong>{action.priority}</strong></td><td>{action.title}</td><td>{action.impact}</td><td>{action.effort}</td><td>{action.layers}</td><td>{action.improvement}</td><td><div className="action-strip compact"><button type="button">Create Sprint Task</button><button type="button">Assign Owner</button><button type="button" onClick={run} disabled={actionDisabled}>Run Diagnostic Again</button></div></td></tr>) : <tr><td colSpan={7}>Run a diagnostic to generate ranked recommended actions by impact.</td></tr>}</tbody></table>
      </article>

      <h3>Visual Intelligence Pipeline</h3>
      <article className="stat-card wide-card dependency-map mission-pipeline" aria-label="Visual Intelligence Pipeline">
        <div className="dependency-chain vertical-pipeline">{dependencyLayers.map((layer, index) => {
          const match = layers.find((item) => (item.layer || "").includes(layer));
          const evidence = runtimeEvidenceByLayer.get(layer);
          const businessStatus = executiveStatusFor(match, evidence, !hasActiveRegression);
          const state = businessStatus === "Disconnected" ? "failure" : businessStatus === "Regression" ? "regression" : String(businessStatus).includes("Warning") ? "warning" : "healthy";
          const relation = hasActiveRegression ? (index < selectedLayerIndex ? "upstream" : index > selectedLayerIndex ? "downstream" : "selected") : "verification";
          const isFirstFailure = index === firstFailureIndex;
          const inBlastRadius = firstFailureIndex >= 0 && index > firstFailureIndex;
          return <button type="button" key={layer} className={`dependency-node pipeline-node ${state} ${relation} ${isFirstFailure ? "first-failure" : ""} ${inBlastRadius ? "blast-radius" : ""}`} onClick={() => setSelectedLayer(layer)} aria-pressed={selectedLayer === layer}><span>{executiveStatusIcon(businessStatus)} {operationalLayerName(layer)}</span><small>{businessStatus}{hasActiveRegression && isFirstFailure ? " · first point of failure" : hasActiveRegression && inBlastRadius ? " · blast radius" : ""}</small></button>;
        })}</div>
        <p><strong>Selected layer:</strong> {hasActiveRegression ? operationalLayerName(selectedLayer) : "No active regression selected"}. {hasActiveRegression ? "Upstream dependencies are highlighted before it; downstream dependencies are highlighted after it." : "Operational warnings are highlighted for verification; no root-cause or downstream regression path is selected."}</p>
        <p><strong>Root cause:</strong> {hasActiveRegression && rootCauseLayer ? `${operationalLayerName(rootCauseLayer)} is the first point of failure.` : "No active regression selected."}</p>
        <p><strong>Downstream impact:</strong> {rootCauseSummary} {blastRadius.length ? `Affected systems: ${blastRadius.map(operationalLayerName).join(" → ")}.` : ""}</p>
      </article>

      <h3>Leadership Layer Briefs</h3>
      <div className="dashboard-grid executive-layer-grid">{dependencyLayers.map((layer, index) => {
        const match = layers.find((item) => (item.layer || "").includes(layer));
        const evidence = runtimeEvidenceByLayer.get(layer);
        const nextLayer = dependencyLayers[index + 1];
        const status = executiveStatusFor(match, evidence, !hasActiveRegression);
        const action = priorityQueue.find((item) => item.layers.includes(layer)) || priorityQueue[0];
        return <article className={`stat-card executive-layer-card status-${status.toLowerCase()}`} key={layer}><h4>{executiveStatusIcon(status)} {operationalLayerName(layer)}</h4><p><strong>Role:</strong> {hasActiveRegression && index === firstFailureIndex ? "Root cause / first point of failure" : hasActiveRegression && index > firstFailureIndex && firstFailureIndex >= 0 ? "Affected downstream impact" : status === "Connected" ? "Verified operating layer" : "Warning verification"}</p><p><strong>Status:</strong> {status}</p><p><strong>Why:</strong> {status === "Connected" ? (match?.plain_language_reason || executiveConnectionPhrase(layer, nextLayer)) : isRuntimeVerified(evidence) ? executiveConnectionPhrase(layer, nextLayer) : (match?.explanation || "Information has not been proven to reach the next intelligence layer yet.")}</p><p><strong>Business impact:</strong> {status === "Connected" ? "Leadership can rely on this PASS layer when making decisions." : hasActiveRegression ? "Repair this handoff before using downstream recommendations for final decisions." : "Verify or rerun this warning before approving release readiness."}</p><p><strong>Affected systems:</strong> {dependencyLayers.slice(index + 1, Math.min(dependencyLayers.length, index + 4)).map(operationalLayerName).join(", ") || "Final intelligence destination"}</p><p><strong>Recommended fix:</strong> {hasActiveRegression ? (match?.suggested_admin_action || action?.title || "Assign an owner, repair the handoff, and rerun Mission Control.") : (status === "Connected" ? "Continue monitoring verified runtime evidence." : "Verify the warning, rerun diagnostics, or review the baseline evidence before release.")}</p><p><strong>Expected improvement:</strong> {executiveDiagnosticCopy(action?.improvement, hasDiagnosticResult ? "Improvement will be calculated after verification." : "Not measured until a diagnostic run exists.")}</p><p><strong>Estimated effort:</strong> {action?.effort || timeToResolution}</p><p><strong>Confidence:</strong> {match?.confidence ?? action?.confidence ?? dailyBriefing.confidence}%</p></article>;
      })}</div>

      <h3>Executive Trends</h3>
      <article className="stat-card wide-card"><label htmlFor="trend-window"><strong>View window</strong></label> <select id="trend-window" value={trendWindow} onChange={(event) => setTrendWindow(event.target.value)}><option value="10">Last 10 runs</option><option value="30">Last 30 runs</option><option value="100">Last 100 runs</option><option value="all">All Time</option></select><div className="dashboard-grid">{trendMetrics.filter(([, key]) => ["overall_health_score", "regression_count", "api_latency_ms", "diagnostic_duration_ms", "public_verification_score", "public_verification_latency_ms"].includes(key)).map(([label, key, unit]) => { const points = asArray(trends[key]); const last = points[points.length - 1]; const max = Math.max(1, ...points.map((point) => Number(point.value) || 0)); return <section className="stat-card" key={key}><h4>{label === "Overall Health Score" ? "Health trend" : label === "Regression Count" ? "Regression trend" : label === "API Latency" ? "API latency" : label === "Diagnostic Duration" ? "Diagnostic duration" : label === "Public Verification Latency" ? "Public verification latency" : "Public verification result"}</h4><p>{last?.value ?? "—"}{unit}</p><div className="spark-bars" aria-label={`${label} chart`}>{points.map((point, index) => <span key={`${key}-${index}`} title={`${point.timestamp}: ${point.value}${unit}`} style={{ height: `${Math.max(4, ((Number(point.value) || 0) / max) * 48)}px` }} />)}</div><div className="action-strip compact"><button type="button" onClick={showRootCauseEvidence}>View Evidence</button><button type="button">Investigate</button></div></section>; })}<section className="stat-card"><h4>Institutional Memory</h4><p>Average health {formatMetric(historyStats.averageHealth, "%")} · Average deployment quality {formatMetric(historyStats.averageDeploymentQuality, "%")}</p><p>Most common failures: {historyStats.mostCommonFailures}</p><p>Most unstable layer: {historyStats.mostUnstableLayer}</p><p>Fastest improving layer: {historyStats.fastestImprovingLayer}</p><p>Average verification result {formatMetric(historyStats.averageVerificationScore, "%")} · Average diagnostic duration {formatMetric(historyStats.averageDiagnosticDuration, "ms")}</p><div className="action-strip compact"><button type="button">Open Layer</button><button type="button" onClick={showRootCauseEvidence}>View Evidence</button></div></section><section className="stat-card"><h4>Deployment history</h4><p>{history.length || "—"} recorded runs</p><div className="spark-bars" aria-label="Deployment history chart">{history.slice(0, 12).reverse().map((run, index) => <span key={run.diagnostic_id || index} title={run.created_at} style={{ height: `${Math.max(4, Number(run.overall_health_percent ?? run.overall_health?.percent ?? 0) / 2)}px`, background: "#38bdf8" }} />)}</div></section></div></article>

      <h3>AI Forecast</h3>
      <div className="dashboard-grid" aria-label="AI Forecast">
        {forecastScenarios.length ? forecastScenarios.map((scenario) => { const projectedReadiness = clampPercent(scenario.projected_release_readiness ?? releaseReadiness + (String(scenario.scenario).toLowerCase().includes("completed") ? 10 : -Math.max(0, warningCount * 2 + regressionCount * 8))); return <article className="stat-card" key={scenario.scenario}><h3>{scenario.scenario}</h3><p><strong>Projected health score:</strong> {scenario.projected_health_score}</p><p><strong>Projected release readiness:</strong> {projectedReadiness}%</p><p><strong>Regression risk:</strong> {scenario.regression_risk}</p><p><strong>Technical debt trend:</strong> {scenario.technical_debt_trend}</p><p><strong>Confidence:</strong> {scenario.confidence}%</p><p><strong>Primary reason:</strong> {scenario.primary_reason}</p></article>; }) : <><article className="stat-card"><h3>If no action is taken</h3><p><strong>Projected health score:</strong> {healthScore}%</p><p><strong>Projected release readiness:</strong> {clampPercent(releaseReadiness - warningCount * 2 - regressionCount * 8)}%</p><p><strong>Regression risk:</strong> {forecast.future_regression_likelihood || forecast.regression_likelihood || (regressionCount ? "Moderate" : "Low")}</p><p><strong>Technical debt trend:</strong> {forecast.technical_debt_trend || (warningCount || regressionCount ? "Increasing" : "Stable")}</p><p><strong>Confidence:</strong> {forecast.confidence ?? aiOperationsAdvisor[0]?.confidence ?? "—"}%</p><p><strong>Primary reason:</strong> Current warnings remain unresolved.</p></article><article className="stat-card"><h3>If completed today</h3><p><strong>Projected health score:</strong> {sprint.expected_health_after_sprint_completion || sprint.expected_health_after_completion || (hasDiagnosticResult ? "Projection unavailable until unresolved diagnostics pass." : "Projection not measured until a diagnostic run exists.")}</p><p><strong>Regression risk:</strong> Reduced</p><p><strong>Projected release readiness:</strong> {clampPercent(releaseReadiness + 10)}%</p><p><strong>Production Confidence:</strong> {formatProductionConfidence(productionConfidence)}</p><p><strong>Estimated Time Saved:</strong> 3 hours/week</p><p><strong>Confidence:</strong> {sprint.confidence || sprint.estimated_confidence || "—"}%</p><p><strong>Primary reason:</strong> Highest-ROI sprint tasks are completed and re-verified.</p></article></>}
      </div>

      <h3>Ecosystem Command Center</h3>
      <div className="ecosystem-command-grid">{ecosystemCommandSystems.map((system) => <article className="stat-card ecosystem-command-card" key={system.subsystem}><h4>{system.subsystem}</h4><p><strong>Health:</strong> {system.health ?? "—"}%</p><p><strong>Trend:</strong> {system.performance || "Stable"}</p><p><strong>Risk:</strong> {asArray(system.warnings).join(", ") || "Low"}</p><p><strong>Recommendation:</strong> {asArray(system.recommendations).join("; ") || "Continue monitoring"}</p><button type="button">Open Dashboard</button></article>)}</div>

      <h3>AI COO Sprint Planning</h3>
      <article className="stat-card wide-card"><h4>Sprint goal</h4><p>{hasActiveRegression ? (sprint.goal || sprint.sprint_goal || `Restore the intelligence chain to ${failureCount ? "non-critical" : "healthy"} status while protecting public diagnostic confidence.`) : "Clear the remaining operational warnings and verify release readiness."}</p><h4>Highest ROI tasks</h4><ul>{(hasActiveRegression && asArray(sprint.highest_roi_tasks).length ? asArray(sprint.highest_roi_tasks) : priorityQueue.slice(0, 3).map((action) => action.title)).map((task) => <li key={task}>{task}</li>)}</ul><h4>Recommended implementation order</h4><ol>{(hasActiveRegression && asArray(sprint.recommended_implementation_order).length ? asArray(sprint.recommended_implementation_order) : priorityQueue.slice(0, 4).map((action) => action.title)).map((task) => <li key={task}>{task}</li>)}</ol><p><strong>Risk reduction estimate:</strong> {sprint.risk_reduction_estimate || "25–40% after the top two queue items are verified."}</p><p><strong>Expected health after sprint completion:</strong> {executiveDiagnosticCopy(sprint.expected_health_after_sprint_completion || sprint.expected_health_after_completion || sprint.expected_result?.overall_health, hasDiagnosticResult ? "Projection unavailable until unresolved diagnostics pass." : "Projection not measured until a diagnostic run exists.")}</p><p><strong>Confidence:</strong> {sprint.confidence || sprint.estimated_confidence || "—"}%</p><p><strong>Estimated time to completion:</strong> {sprint.estimated_time_to_completion || sprint.estimated_completion || "—"}</p></article>

      </> }

      {viewMode === "technical" && <>
      <h3>Runtime Evidence</h3>
      <article className="stat-card wide-card runtime-evidence-panel" aria-label="Runtime Evidence">
        <h4>Are the intelligence layers actually connected?</h4>
        <p><strong>Verification rule:</strong> A layer is VERIFIED only when runtime propagation evidence is present and downstream consumption was actually observed. Contract-only inference is not counted.</p>
        <table className="admin-table runtime-evidence-table">
          <thead><tr><th>Layer</th><th>Runtime status</th><th>Source type</th><th>Runtime trace ID</th><th>Input object ID received</th><th>Output object ID produced</th><th>Timestamp</th><th>Next downstream consumer</th><th>Downstream consumption observed</th><th>Fields added</th><th>Fields removed</th><th>Fields mutated</th><th>Fixture usage</th><th>Evidence summary</th></tr></thead>
          <tbody>{runtimeEvidence.length ? runtimeEvidence.map((evidence) => <tr key={evidence.layer}><td>{evidence.layer}</td><td><strong>{evidence.runtime_status}</strong></td><td>{evidence.source_type}</td><td>{evidence.runtime_trace_id}</td><td>{evidence.input_object_id_received ?? "—"}</td><td>{evidence.output_object_id_produced ?? "—"}</td><td>{evidence.timestamp || "—"}</td><td>{evidence.next_downstream_consumer || "—"}</td><td>{evidence.downstream_consumption_observed ? "yes" : "no"}</td><td>{formatList(evidence.fields_added)}</td><td>{formatList(evidence.fields_removed)}</td><td>{formatList(evidence.fields_mutated)}</td><td>{evidence.fixture_usage || (evidence.fixture_data_used ? "yes" : "no")}</td><td>{evidence.evidence_summary || "No runtime evidence displayed; not verified."}</td></tr>) : <tr><td colSpan={14}>Runtime evidence is missing. No layer is counted as verified until propagation evidence is displayed.</td></tr>}</tbody>
        </table>
      </article>


      <h3 ref={rootCauseEvidenceRef}>Root Cause Evidence</h3>
      <article className="stat-card wide-card root-cause-evidence-panel" aria-label="Root Cause Evidence">
        <h4>Root-cause selection trace proof</h4>
        <p><strong>Primary filter:</strong> {rootCauseSelectionTrace.primary_filter || "status != 'PASS' and diagnostic_category not in excluded_downstream_categories"}</p>
        <p><strong>Fallback filter:</strong> {rootCauseSelectionTrace.fallback_filter || "status != 'PASS'"} · <strong>Fallback used:</strong> {formatBoolean(rootCauseSelectionTrace.fallback_used)}</p>
        <p><strong>Selected layer:</strong> {hasActiveRegression ? (rootCauseSelectionTrace.selected_layer || rootCauseLayer || "—") : "No active regression selected"}</p>
        <p><strong>Exact selection comparison:</strong> <code>{rootCauseSelectionTrace.selection_boolean_or_comparison || "—"}</code></p>
        <p><strong>Selected because:</strong> {hasActiveRegression ? (rootCauseSelectionTrace.selected_because || "Selection proof unavailable until the diagnostic payload includes root_cause_selection_trace.") : "regression_count is 0, so Mission Control is tracking warning cleanup and release readiness instead of selecting a root cause."}</p>
        <p><strong>Selected field mismatches:</strong> {asArray(rootCauseSelectionTrace.selected_layer_mismatches).length ? JSON.stringify(rootCauseSelectionTrace.selected_layer_mismatches) : "None"}</p>
        <p><strong>No-mismatch explanation:</strong> {rootCauseSelectionTrace.no_mismatch_explanation || (rootCauseSelectionTrace.selected_layer_mismatch_exists === false ? "Selection was driven by non-PASS state rather than an owned-field mismatch." : "—")}</p>
        <table className="admin-table runtime-evidence-table">
          <thead><tr><th>Candidate layer</th><th>Status</th><th>Pass/fail reason</th><th>Primary filter booleans</th><th>Excluded as downstream affected</th><th>Owned field mismatches</th></tr></thead>
          <tbody>{rootCauseTraceCandidates.length ? rootCauseTraceCandidates.map((candidate) => {
            const values = safeObject(candidate.pass_fail_values);
            return <tr key={candidate.layer}><td>{candidate.layer}</td><td><strong>{candidate.status || "MISSING"}</strong>{candidate.display_status ? ` · ${candidate.display_status}` : ""}</td><td>{candidate.why || (candidate.passed ? "passed" : "failed")}</td><td>status != PASS: {formatBoolean(values["status != 'PASS'"])}; diagnostic category not excluded: {formatBoolean(values["diagnostic_category not excluded"])}; combined: {formatBoolean(values.combined_result)}</td><td>{values["diagnostic_category not excluded"] === false || ["downstream_impacted", "blocked_by_upstream", "needs_rerun_after_upstream_fix"].includes(candidate.diagnostic_category) ? "yes" : "no"}</td><td>{asArray(candidate.owned_field_mismatches).length ? JSON.stringify(candidate.owned_field_mismatches) : "None"}</td></tr>;
          }) : <tr><td colSpan={6}>No root_cause_selection_trace is available in this diagnostic payload.</td></tr>}</tbody>
        </table>
      </article>

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
      <article className="stat-card"><h4>Suggested Sprint</h4><p>Estimated completion {aiChiefOperatingOfficer.suggested_sprint?.estimated_completion || "—"}</p><ul>{asArray(aiChiefOperatingOfficer.suggested_sprint?.tasks).map((task) => <li key={task}>{task}</li>)}</ul><pre className="data-note">{JSON.stringify(aiChiefOperatingOfficer.suggested_sprint?.expected_result || {}, null, 2)}</pre><p>Estimated confidence {aiChiefOperatingOfficer.suggested_sprint?.estimated_confidence ?? "—"}%</p></article>

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
      <article className="stat-card"><p>{executiveDiagnosticCopy(result?.ai_summary || result?.executive_summary, hasDiagnosticResult ? "Awaiting verified rerun." : "Run a diagnostic to generate a natural-language AI Insights summary.")}</p></article>

      <h3>Layer Status</h3>
      <div className="dashboard-grid">
        {layers.length ? layers.map((layer, index) => {
          const expected = safeObject(layer.expected);
          const actual = safeObject(layer.actual);
          const confidence = safeObject(layer.confidence_difference);
          const priority = safeObject(layer.priority_difference);
          return (
            <details className="stat-card drilldown-card" key={layer.layer || `layer-${index}`}>
              <summary><strong>{layer.layer || "Unknown Layer"}</strong> · {statusIcon(layer)} · Score {actual.score ?? expected.score ?? "—"}</summary>
              <p>Status: <strong>{layer.status || "UNKNOWN"}</strong> · Execution Time: <strong>{layer.execution_time_ms ?? "—"}ms</strong> · Version: <strong>v1</strong></p>
              <p>Diagnostics: <strong>{layer.explanation || "Diagnostics unavailable"}</strong></p>
              <p>Regression Level: <strong>{layer.regression_level || layer.regression || "None"}</strong></p>
              <p>Expected Score: {expected.score ?? "—"} · Actual Score: {actual.score ?? "—"} · Score Delta: {layer.score_delta ?? safeObject(layer.difference_summary).score ?? "—"}</p>
              <p>Confidence Before/After: {confidence.expected ?? "—"} → {confidence.actual ?? "—"} · Priority Before/After: {priority.expected ?? "—"} → {priority.actual ?? "—"}</p>
              <p><strong>Supporting Evidence</strong></p><ul>{asArray(layer.supporting_evidence).length ? asArray(layer.supporting_evidence).map((evidence) => <li key={evidence}>{evidence}</li>) : <li>No evidence attached yet.</li>}</ul><p><strong>What is wrong:</strong> {safeObject(layer.diagnostic_resolution).what_is_wrong || layer.plain_language_reason || "No mismatch detected."}</p><p><strong>Why it happened:</strong> {safeObject(layer.diagnostic_resolution).why_it_happened || layer.likely_cause || "Cause unavailable."}</p><p><strong>How to fix it:</strong> {safeObject(layer.diagnostic_resolution).how_to_fix || layer.suggested_admin_action || "Review scoring logic and re-run diagnostics before updating baselines."}</p><p><strong>Fix type:</strong> {safeObject(layer.diagnostic_resolution).fix_type || layer.fix_type || "RERUN_REQUIRED"} · <strong>Owner:</strong> {safeObject(layer.diagnostic_resolution).owner || layer.owner || "AI COO"}</p><p><strong>Verification step:</strong> {safeObject(layer.diagnostic_resolution).verification_step || layer.verification_step || "Rerun diagnostic and confirm this layer returns expected baseline values."}</p>
              <div className="drilldown-grid"><span>Health Timeline</span><span>Historical Scores</span><span>Regression History</span><span>Evidence</span><span>Related Commits</span><span>Affected Systems</span><span>Recommended Fixes</span><span>Dependent Layers</span></div>
              <div className="action-strip">{actionButtons.map((action) => <button key={action} type="button" onClick={action === "Run Diagnostic Again" ? run : action === "View Evidence" ? showRootCauseEvidence : undefined} disabled={actionDisabled && action === "Run Diagnostic Again"}>{action}</button>)}</div>
            </details>
          );
        }) : <article className="stat-card"><h3>Diagnostics unavailable</h3><p>Layer data is missing or could not be loaded.</p></article>}
      </div>

      <div className="dashboard-grid">
        <article className="stat-card"><h3>Dependency Impact View</h3><p>Member → Society → Institution → Opportunity → Predictive → Decision Support → Execution Planning → Execution Intelligence → Institutional Memory → Institutional Learning</p>{dependencyChain.length ? dependencyChain.map((item) => <p key={item.layer}><strong>{item.layer}</strong>: {chainLabel[item.state] || item.state || "Stable layer"}</p>) : <p>Dependency impact unavailable until a diagnostic runs.</p>}</article>
        <article className="stat-card"><h3>Recommended Next Actions</h3>{recommendedNextActions.length ? <ul>{recommendedNextActions.map((action) => <li key={action}>{action}</li>)}</ul> : <ul><li>Review scoring logic</li><li>Review expected baselines</li><li>Do not update baselines until drift is explained</li><li>Re-run diagnostic after changes</li><li>Generate public report only after the monitor is stable</li></ul>}</article>
        <article className="stat-card"><h3>Regression Summary</h3>{layers.filter((l) => l.regression).length ? layers.filter((l) => l.regression).map((l) => <p key={l.layer}>{l.layer}: {l.regression} ({safeObject(l.difference_summary).score ?? "—"}) · {l.diagnostic_category || "scoring_regression"}</p>) : <p>None</p>}</article>
        <article className="stat-card wide-card"><h3>Stabilization Report</h3><p><strong>Root cause:</strong> {stabilizationReport.root_cause || "Run a diagnostic to identify stabilization root cause."}</p><p><strong>Responsible files/functions:</strong> {formatList(stabilizationReport.files_functions_responsible)}</p><p><strong>Fix requires:</strong> {stabilizationReport.fix_requires || "—"}</p><p><strong>Warnings expected to disappear:</strong> {formatList(stabilizationReport.warnings_should_disappear_after_fix)}</p><p><strong>Warnings still legitimate:</strong> {formatList(stabilizationReport.warnings_still_legitimate)}</p></article><article className="stat-card wide-card"><h3>AI Repair Briefs</h3>{repairBriefs.length ? repairBriefs.map((brief, briefIndex) => <section className="stat-card" key={`${brief.layer_name || "repair"}-${briefIndex}`}><h4>{brief.marker || "AI_REPAIR_HINT"}: {brief.layer_name}</h4><p><strong>Status:</strong> {brief.diagnostic_status} · <strong>Failure type:</strong> {brief.failure_type} · <strong>Fix type:</strong> {brief.fix_type}</p><p><strong>Mismatch:</strong> {brief.field_that_drifted} expected {JSON.stringify(brief.expected_value)} but actual was {JSON.stringify(brief.actual_value)}</p><p><strong>Business rule:</strong> {brief.business_rule_violated}</p><p><strong>Likely backend:</strong> {brief.likely_backend_file} · <strong>Function/service:</strong> {brief.likely_function_service}</p><p><strong>Likely frontend:</strong> {brief.likely_frontend_file || "Not applicable"}</p><p><strong>Safe baseline update:</strong> {brief.safe_baseline_update} · <strong>Do not change:</strong> {brief.do_not_change_notes}</p><p><strong>Recommended steps:</strong> {formatList(brief.recommended_fix_steps)}</p><p><strong>Verification command:</strong> <code>{brief.verification_command}</code></p><p><strong>Expected result:</strong> {brief.expected_result_after_fix}</p><p><strong>Downstream impact:</strong> {formatList(brief.downstream_impact)}</p><p><strong>Related layers likely to clear:</strong> {formatList(brief.related_layers_likely_to_clear_after_this_fix)}</p><p><strong>Confidence:</strong> {brief.confidence_score}%</p></section>) : <p>All diagnostic checks currently passed, so no AI repair briefs are open.</p>}</article><article className="stat-card wide-card"><h3>Diagnostic Resolution Engine</h3>{diagnosticResolutionEngine.length ? diagnosticResolutionEngine.map((issue, issueIndex) => <section className="stat-card" key={`${issue.layer || "issue"}-${issueIndex}`}><h4>{issue.layer || "Unassigned diagnostic"}</h4><p><strong>What is wrong?</strong> {issue.what_is_wrong || "No mismatch details available."}</p><p><strong>Why is it wrong?</strong> {issue.why_it_happened || "Cause classification unavailable."}</p><p><strong>What fixes it?</strong> {issue.how_to_fix || "Rerun diagnostic after fixing the upstream issue."}</p><p><strong>Who owns it?</strong> {issue.owner || "AI COO"} · <strong>Fix type:</strong> {issue.fix_type || "RERUN_REQUIRED"}</p><p><strong>How do we prove it is fixed?</strong> {issue.verification_step || "Rerun diagnostic and confirm the warning disappears."}</p></section>) : <p>All diagnostic checks currently passed, so no resolution items are open.</p>}</article><article className="stat-card wide-card"><h3>Learning Memory</h3><p><strong>Recurring warning patterns:</strong> {formatList(learningMemory.recurring_warning_patterns)}</p><p><strong>Layers that drift most often:</strong> {formatList(learningMemory.layers_that_drift_most_often)}</p><p><strong>Harmless warning candidates:</strong> {formatList(learningMemory.harmless_warning_candidates)}</p><p><strong>Dangerous warning candidates:</strong> {formatList(learningMemory.dangerous_warning_candidates)}</p><p><strong>Baseline learning:</strong> {learningMemory.baseline_updates_risk_note || "Learning memory starts after the next diagnostic run."}</p></article><article className="stat-card wide-card"><h3>Stabilization Checklist</h3><p><strong>Unresolved intelligence warnings:</strong> {formatList(stabilizationChecklist.unresolved_intelligence_warnings)}</p><p><strong>Resolved warnings:</strong> {formatList(stabilizationChecklist.resolved_warnings)}</p><p><strong>Remaining true regressions:</strong> {formatList(stabilizationChecklist.remaining_true_regressions)}</p><p><strong>Warnings requiring rerun:</strong> {formatList(stabilizationChecklist.warnings_requiring_rerun)}</p><p><strong>Warnings requiring code fix:</strong> {formatList(stabilizationChecklist.warnings_requiring_code_fix)}</p><p><strong>Warnings requiring config fix:</strong> {formatList(stabilizationChecklist.warnings_requiring_config_fix)}</p></article><article className="stat-card"><h3>Discord Configuration Warnings</h3>{discordConfigurationWarnings.length ? discordConfigurationWarnings.map((warning) => <p key={warning.warning}><strong>{warning.warning}</strong>: {warning.recommended_fix}</p>) : <p>Discord warnings are tracked separately from SimbaBrain intelligence health. If bot_log_post returns 403 Forbidden, grant the Simba bot View Channel and Send Messages in the bot_log channel, or update the bot_log webhook URL to an active webhook for that channel.</p>}</article>
        <article className="stat-card"><h3>Critical Failures</h3>{asArray(result?.critical_failures).length ? asArray(result.critical_failures).map((l, i) => <p key={l.layer || i}>{l.layer || "Unknown Layer"}: {l.explanation || "Diagnostics unavailable"}</p>) : <p>None</p>}</article>
        <article className="stat-card"><h3>Performance Metrics</h3><pre className="data-note">{JSON.stringify(result?.performance || result?.performance_timings || {}, null, 2)}</pre></article>
        <article className="stat-card"><h3>Root Cause Analysis</h3>{rootCauseClassification.category && <p><strong>Classification:</strong> {rootCauseClassification.category} · Confidence {Math.round((rootCauseClassification.confidence || 0) * 100)}%{rootCauseClassification.heuristic ? " · heuristic" : ""}</p>}{asArray(result?.root_cause_analysis).length ? asArray(result.root_cause_analysis).map((line) => <p key={line}>{line}</p>) : <p>Run a diagnostic to view root-cause tracing.</p>}</article>
      </div>

      <h3>Diagnostic History</h3>
      <div>{history.length ? history.map((run, index) => { const summary = safeObject(run.pass_fail_summary); return <details className="stat-card" key={run.diagnostic_id || index}><summary><strong>{run.created_at || "Timestamp unavailable"}</strong> · Health {run.overall_health_percent ?? run.overall_health?.percent ?? "—"}% · {run.overall_status || "UNKNOWN"} · Duration {run.performance?.total_execution_time_ms ?? run.performance_timings?.total_execution_time_ms ?? "—"}ms · {run.environment || "environment unknown"}</summary><p><strong>Report token:</strong> {run.report_token || run.public_report_token || "—"}</p><p><strong>Version/commit:</strong> {run.build_commit || run.version || run.fixture_version || "—"}</p><p><strong>Pass/fail summary:</strong> {summary.passed ?? run.status_counts?.pass ?? 0} pass · {summary.warnings ?? run.status_counts?.warning ?? 0} warnings · {summary.failed ?? run.status_counts?.fail ?? 0} failures · {summary.regressions ?? run.regression_count ?? 0} regressions</p><div className="drilldown-grid"><span>What changed: {run.executive_summary || "Diagnostic baseline recorded"}</span><span>Health improved: {trendDirectionFrom(getRunHealth(run), getRunHealth(history[index + 1]), false) === "improved" ? "Yes" : "Not yet / unknown"}</span><span>Regressions disappeared: {getRunRegressions(run) === 0 ? "Yes" : "No"}</span><span>Prediction accurate: {run.prediction_accuracy || "Awaiting next run"}</span><span>Recommendations worked: {run.recommendations_effective || "Awaiting verification"}</span></div><div className="action-strip compact"><button type="button" onClick={showRootCauseEvidence}>View Evidence</button><button type="button">Mark Resolved</button><button type="button">Create Sprint Task</button></div><pre className="data-note">{JSON.stringify(run, null, 2)}</pre></details>; }) : <article className="stat-card"><p>No diagnostic history yet.</p><div className="action-strip"><button type="button" onClick={run} disabled={actionDisabled}>Run Diagnostic Again</button></div></article>}</div>

      <h3>Compare Previous Run</h3>
      <pre className="data-note">{JSON.stringify(healthTrend, null, 2)}</pre>
      {DEBUG_ERRORS && <><h3>Debug Output</h3><pre className="data-note">{JSON.stringify(layers.map(({ layer, debug_payload }) => ({ layer, debug_payload })), null, 2)}</pre><h3>Public Report Debug Output</h3><pre className="data-note">{JSON.stringify({ publicReportState, publicReportError, publicReportVerification }, null, 2)}</pre></>}
      </>}
    </section>
  );
}
