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
  resourceGenerator: "ResourceGenerator",
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

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
  const answers = (payload.responses || []).map((value) => Number(value || 3));
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

  return {
    userId: payload.userId,
    percentages,
    roles: {
      primary: ranked[0]?.label || "Architect",
      secondary: ranked[1]?.label || "Operator",
      growth: ranked[ranked.length - 2]?.label || "Educator",
      shadow: ranked[ranked.length - 1]?.label || "Nurturer",
    },
    coaching:
      "Simulation mode: backend unavailable. Connect VITE_API_BASE_URL to persist live assessments.",
    insights: {
      primary: `Simulation primary role: ${ranked[0]?.label || "Architect"}.`,
      shadow: `Simulation shadow role: ${ranked[ranked.length - 1]?.label || "Nurturer"}.`,
      growth: `Simulation growth role: ${ranked[ranked.length - 2]?.label || "Educator"}.`,
    },
  };
}

function normalizeResponse(raw, fallbackUserId) {
  const base = raw && typeof raw === "object" ? raw : {};
  const percentages = normalizePercentages(base.percentages);
  const ranked = sortedRoles(percentages);

  return {
    userId: base.userId || fallbackUserId,
    percentages,
    roles: {
      primary: base.roles?.primary || ranked[0]?.label || "Architect",
      secondary: base.roles?.secondary || ranked[1]?.label || "Operator",
      growth: base.roles?.growth || ranked[ranked.length - 2]?.label || "Educator",
      shadow: base.roles?.shadow || ranked[ranked.length - 1]?.label || "Nurturer",
    },
    coaching:
      base.coaching ||
      `Your strongest pattern is ${ranked[0]?.label || "Architect"}. Focus on growth in ${ranked[ranked.length - 2]?.label || "Educator"}.`,
    insights: {
      primary: base.insights?.primary || "",
      shadow: base.insights?.shadow || "",
      growth: base.insights?.growth || "",
    },
  };
}

function cacheResult(result) {
  const store = readStore();
  store[result.userId] = result;
  writeStore(store);
}

export async function submitLeadershipAssessment(payload) {
  const requestPayload = {
    userId: payload.userId,
    responses: payload.answers,
  };

  let result;
  if (!API_BASE) {
    result = simulateAssessmentResult(requestPayload);
  } else {
    try {
      const res = await fetch(`${API_BASE}/assessment/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      });
      if (!res.ok) throw new Error(`Assessment API failed (${res.status})`);
      const data = await res.json();
      result = normalizeResponse(data, payload.userId);
    } catch {
      result = simulateAssessmentResult(requestPayload);
    }
  }

  cacheResult(result);
  return result;
}

export async function fetchLeadershipResultByUserId(userId) {
  if (!userId) return null;

  if (API_BASE) {
    try {
      const res = await fetch(`${API_BASE}/assessment/results/${encodeURIComponent(userId)}`);
      if (res.ok) {
        const data = await res.json();
        const normalized = normalizeResponse(data, userId);
        cacheResult(normalized);
        return normalized;
      }
    } catch {
      // fallback to local cache below
    }
  }

  const store = readStore();
  return store[userId] || null;
}

export { ROLE_LABELS, ROLE_KEYS };
