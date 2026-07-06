import { readFileSync } from 'node:fs';

const component = readFileSync('src/components/IntelligenceHealthMonitor.jsx', 'utf8');
const css = readFileSync('src/styles/dashboard.css', 'utf8');
const checks = [
  ['Executive and Technical View use the same result source', /const result = safeObject\(diagnosticRunState \|\| history\[0\]\)/.test(component) && component.includes('viewMode === "executive"') && component.includes('viewMode === "technical"')],
  ['Diagnostic action buttons are visible and wired to handlers', component.includes('Run Full Intelligence Diagnostic') && component.includes('Generate Public Diagnostic Report') && /<button className="hero-btn" type="button" onClick=\{run\}/.test(component) && /<button className="hero-btn secondary" type="button" onClick=\{generateReport\}/.test(component)],
  ['Fallback data is not treated as a root-cause diagnostic result', /const firstFailureIndex = hasDiagnosticResult && hasActiveRegression \?/.test(component) && component.includes('const hasActiveRegression = regressionCount > 0;') && component.includes(': -1;')],
  ['Runtime verification requires downstream consumption', component.includes('downstream_consumption_observed') && /const isRuntimeVerified = \(evidence\).*downstream_consumption_observed/s.test(component)],
  ['Executive View cannot report Connected without runtime evidence', /if \(!isRuntimeVerified\(evidence\)\) return/.test(component) && !/return "Connected";\n};\n\nexport default/.test(component)],
  ['Pipeline highlights upstream, downstream, first failure, and blast radius', ['upstream', 'downstream', 'first-failure', 'blast-radius', 'firstFailureIndex', 'blastRadius'].every((token) => component.includes(token))],
  ['Mission Control health surfaces avoid placeholder health percentages', !/(45%|47%|71%|73%|75%|77%|78%|80%|90%\+|91%|92%|94%)/.test(component)],
  ['Ecosystem Command Center only renders diagnostic subsystems', /const ecosystemCommandSystems = asArray\(ecosystemIntelligence\.subsystems\);/.test(component) && !component.includes('Math.max(72, Number(healthScore)')],
  ['Mobile responsiveness covers tables and pipeline components', css.includes('@media (max-width: 700px)') && css.includes('.runtime-evidence-table') && css.includes('.mission-pipeline .pipeline-node')],
  ['Root Cause Evidence exposes the selection trace and View Evidence navigation', component.includes('root_cause_selection_trace') && component.includes('Root Cause Evidence') && component.includes('rootCauseTraceCandidates') && component.includes('selection_boolean_or_comparison') && component.includes('selected_layer_mismatches') && component.includes('no_mismatch_explanation') && component.includes('showRootCauseEvidence') && /View Evidence[\s\S]*showRootCauseEvidence/.test(component)],
  ['Zero-regression Mission Control avoids stale root-cause narrative', component.includes('No active regression selected') && component.includes('Clear remaining operational warnings') && component.includes('Verify release readiness') && component.includes('warningVerificationQueue') && /const rootCauseSummary = hasActiveRegression && rootCauseLayer/.test(component)],
  ['Executive metrics separate platform health, release readiness, production confidence, and risk', component.includes('deriveExecutiveRisk') && component.includes('deriveMissionStatus') && component.includes('const releaseReadiness = clampPercent') && component.includes('const productionConfidence = clampPercent') && component.includes('const executiveRisk = commandCenter.executive_risk') && component.includes('Platform Health') && component.includes('Release Readiness') && component.includes('Executive Risk')],
  ['AI Forecast projects both health and release readiness', component.includes('Projected health score') && component.includes('Projected release readiness') && component.includes('projected_release_readiness')],
  ['Production confidence is measured from diagnostics and evidence instead of a placeholder', !component.includes('Production confidence not measured') && !component.includes('production confidence not measured') && component.includes('verifiedReruns') && component.includes('deploymentEvidenceVerified') && component.includes('diagnosticsPassed')],
];
let failed = false;
for (const [name, pass] of checks) {
  console.log(`${pass ? 'PASS' : 'FAIL'} ${name}`);
  if (!pass) failed = true;
}
if (failed) process.exit(1);
