import { firstSevenDaysPathway } from "./memberOnboardingConfig";

const STORAGE_PREFIX = "simba_member_onboarding";

function storageKey(memberId) {
  return `${STORAGE_PREFIX}:${memberId || "guest"}`;
}

function safeParse(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export function getMemberOnboardingState(memberId) {
  if (typeof window === "undefined") return createInitialOnboardingState();
  return safeParse(window.localStorage.getItem(storageKey(memberId))) || createInitialOnboardingState();
}

export function createInitialOnboardingState() {
  return {
    onboarding_started_at: null,
    onboarding_completed_at: null,
    completed_steps: [],
    current_step: firstSevenDaysPathway[0]?.key || null,
  };
}

export function saveMemberOnboardingState(memberId, state) {
  if (typeof window === "undefined") return state;
  window.localStorage.setItem(storageKey(memberId), JSON.stringify(state));
  return state;
}

export function mergeDetectedOnboardingSteps(state, detectedSteps = []) {
  const completed = Array.from(new Set([...(state.completed_steps || []), ...detectedSteps]));
  return finalizeOnboardingState({ ...state, completed_steps: completed });
}

export function startMemberOnboarding(state) {
  return finalizeOnboardingState({
    ...state,
    onboarding_started_at: state.onboarding_started_at || new Date().toISOString(),
    current_step: state.current_step || firstSevenDaysPathway[0]?.key || null,
  });
}

export function completeMemberOnboardingStep(state, stepKey) {
  const completed = Array.from(new Set([...(state.completed_steps || []), stepKey]));
  return finalizeOnboardingState({
    ...state,
    onboarding_started_at: state.onboarding_started_at || new Date().toISOString(),
    completed_steps: completed,
  });
}

function finalizeOnboardingState(state) {
  const completed = new Set(state.completed_steps || []);
  const nextStep = firstSevenDaysPathway.find((step) => !completed.has(step.key));
  return {
    ...state,
    completed_steps: Array.from(completed),
    current_step: nextStep?.key || firstSevenDaysPathway[firstSevenDaysPathway.length - 1]?.key || null,
    onboarding_completed_at: nextStep ? state.onboarding_completed_at || null : state.onboarding_completed_at || new Date().toISOString(),
  };
}
