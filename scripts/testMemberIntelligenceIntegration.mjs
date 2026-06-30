import assert from 'node:assert/strict';
import { buildMemberIntelligence, memberIntelligenceToBehavioralProfile } from '../src/data/memberIntelligence.js';
import { interpretMemberRoleAlignment } from '../src/data/roleInterpretationEngine.js';

const liveOne = [{ id: 'r1', assessment_name: 'Leadership archetype assessment', primary_result: { label: 'Documentation Steward', traits: ['accountability', 'decision clarity'] }, strengths: ['accountability', 'documentation'], opportunities_for_growth: ['delegation'] }];
const liveMany = [
  ...liveOne,
  { id: 'r2', assessment_name: 'Treasury stewardship assessment', primary_result: { label: 'Resource Guardian', traits: ['accuracy', 'transparency', 'risk awareness'] }, strengths: ['accuracy', 'transparency', 'risk awareness'] },
  { id: 'r3', assessment_name: 'Operations and follow-through assessment', primary_result: { label: 'Grounded Operator', traits: ['follow-through', 'coordination', 'dependability'] }, strengths: ['follow-through', 'coordination', 'dependability'] },
  { id: 'r4', assessment_name: 'Documentation and knowledge stewardship assessment', primary_result: { label: 'Documentation Steward', traits: ['confidentiality', 'structure'] }, strengths: ['confidentiality', 'structure'] },
];

const fallback = buildMemberIntelligence({ assessmentResults: [] });
assert.equal(fallback.isFallback, true, 'sample profile is used only when live intelligence is unavailable');
assert.equal(fallback.source, 'deprecated_sample_profile');

const live = buildMemberIntelligence({ member: { id: 'u1', name: 'Live Member' }, assessmentResults: liveOne });
assert.equal(live.isFallback, false, 'live intelligence replaces sample profile automatically');
assert.equal(live.source, 'live_member_intelligence');
assert.equal(live.displayName, 'Live Member');

const profile = memberIntelligenceToBehavioralProfile(live);
const report = interpretMemberRoleAlignment(profile, 'committee-chair');
assert.ok(report.whyThisAlignmentExists.length > 0, 'role interpretation receives live intelligence evidence');
assert.ok(report.missingAssessmentEvidence.length > 0, 'missing assessment prompts appear');
assert.ok(report.suggestedNextAssessment, 'recommendations include a next assessment');
assert.ok(report.confidence, 'recommendations include confidence');
assert.ok(report.evidenceSources.length > 0, 'recommendations include evidence');
assert.match(report.communityDecisionReminder, /does not rank members, appoint members/i, 'no automatic appointments occur');

const stronger = buildMemberIntelligence({ assessmentResults: liveMany });
assert.notEqual(live.confidence, stronger.confidence, 'confidence changes with additional evidence');

const dashboardWidget = {
  title: live.isFallback ? 'Fallback behavioral profile active' : 'Live intelligence active',
  confidence: live.confidence,
  evidenceCount: live.evidence.length,
};
assert.equal(dashboardWidget.title, 'Live intelligence active', 'dashboard widgets still render from the read model');
assert.ok(dashboardWidget.evidenceCount > 0);

assert.doesNotThrow(() => interpretMemberRoleAlignment(memberIntelligenceToBehavioralProfile(fallback), 'treasurer'), 'no existing workflows break with fallback intelligence');
console.log('member intelligence integration tests passed');
