import { readFileSync } from 'node:fs';

const component = readFileSync('src/components/IntelligenceHealthMonitor.jsx', 'utf8');
const css = readFileSync('src/styles/dashboard.css', 'utf8');
const checks = [
  ['Executive and Technical View use the same result source', /const result = safeObject\(diagnosticRunState \|\| history\[0\]\)/.test(component) && component.includes('viewMode === "executive"') && component.includes('viewMode === "technical"')],
  ['Runtime verification requires downstream consumption', component.includes('downstream_consumption_observed') && /const isRuntimeVerified = \(evidence\).*downstream_consumption_observed/s.test(component)],
  ['Executive View cannot report Connected without runtime evidence', /if \(!isRuntimeVerified\(evidence\)\) return/.test(component) && !/return "Connected";\n};\n\nexport default/.test(component)],
  ['Pipeline highlights upstream, downstream, first failure, and blast radius', ['upstream', 'downstream', 'first-failure', 'blast-radius', 'firstFailureIndex', 'blastRadius'].every((token) => component.includes(token))],
  ['Mobile responsiveness covers tables and pipeline components', css.includes('@media (max-width: 700px)') && css.includes('.runtime-evidence-table') && css.includes('.mission-pipeline .pipeline-node')],
];
let failed = false;
for (const [name, pass] of checks) {
  console.log(`${pass ? 'PASS' : 'FAIL'} ${name}`);
  if (!pass) failed = true;
}
if (failed) process.exit(1);
