const STORAGE_KEY = "leadership_results_v1";

const ROLE_KEYS = [
  "architect",
  "operator",
  "steward",
  "builder",
  "connector",
  "protector",
  "nurturer",
  "educator",
  "resourceGenerator",
];

const ROLE_LABELS = {
  architect: "Architect",
  operator: "Operator",
  steward: "Steward",
  builder: "Builder",
  connector: "Connector",
  protector: "Protector",
  nurturer: "Nurturer",
  educator: "Educator",
  resourceGenerator: "Resource Generator",
};

const API_URL = import.meta.env.VITE_LEADERSHIP_API_URL || "";

function readStore() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function writeStore(store) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function normalizePercentages(raw = {}) {
  const normalized = {};
  ROLE_KEYS.forEach((key) => {
    normalized[key] = Number(raw[key] || 0);
  });
  return normalized;
}

function sortedRoles(percentages) {
  return Object.entries(percentages)
    .map(([key, value]) => ({ key, label: ROLE_LABELS[key] || key, value }))
    .sort((a, b) => b.value - a.value);
}

function simulateAssessmentResult(payload) {
  const answers = (payload.answers || []).map((value) => Number(value || 3));
  const buckets = ROLE_KEYS.reduce((acc, role) => ({ ...acc, [role]: 0 }), {});

  answers.forEach((answer, index) => {
    const role = ROLE_KEYS[index % ROLE_KEYS.length];
    buckets[role] += answer;
  });

  const maxScore = Math.ceil(answers.length / ROLE_KEYS.length) * 5;
  const percentages = ROLE_KEYS.reduce((acc, role) => {
    acc[role] = Math.round(((buckets[role] || 0) / maxScore) * 100);
    return acc;
  }, {});

  const ranked = sortedRoles(percentages);
  const roles = {
    primary: ranked[0]?.label || "Architect",
    secondary: ranked[1]?.label || "Operator",
    growth: ranked[ranked.length - 2]?.label || "Educator",
    shadow: ranked[ranked.length - 1]?.label || "Nurturer",
  };

  const coaching = `Your leadership center is ${roles.primary}. Pair it with ${roles.secondary} for strongest execution. Build ${roles.growth} next, and watch for overuse patterns in ${roles.shadow}.`;

  return {
    userId: payload.userId,
    percentages,
    roles,
    coaching,
  };
}

function normalizeResponse(raw, payload) {
  const base = raw && typeof raw === "object" ? raw : {};
  const percentages = normalizePercentages(base.percentages);
  const ranked = sortedRoles(percentages);

  return {
    userId: base.userId || payload.userId,
    percentages,
    roles: {
      primary: base.roles?.primary || ranked[0]?.label || "Architect",
      secondary: base.roles?.secondary || ranked[1]?.label || "Operator",
      growth: base.roles?.growth || ranked[ranked.length - 2]?.label || "Educator",
      shadow: base.roles?.shadow || ranked[ranked.length - 1]?.label || "Nurturer",
    },
    coaching:
      base.coaching ||
      `Your strongest pattern is ${ranked[0]?.label || "Architect"}. Focus on deliberate reps in your growth role to unlock balance.`,
  };
}

export async function submitLeadershipAssessment(payload) {
  const requestPayload = {
    userId: payload.userId,
    answers: payload.answers,
  };

  let result;
  if (!API_URL) {
    result = simulateAssessmentResult(requestPayload);
  } else {
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      });
      if (!res.ok) {
        throw new Error(`Leadership API failed (${res.status})`);
      }
      const data = await res.json();
      result = normalizeResponse(data, requestPayload);
    } catch {
      result = simulateAssessmentResult(requestPayload);
    }
  }

  const store = readStore();
  store[result.userId] = result;
  writeStore(store);

  return result;
}

export function getLeadershipResultByUserId(userId) {
  const store = readStore();
  return store[userId] || null;
}

export { ROLE_LABELS };
