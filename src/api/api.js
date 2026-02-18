import { API_BASE_URL } from "../config";

const PROTOTYPE_USER = {
  id: "prototype-user",
  role: "admin",
  is_admin: true,
  display_name: "Prototype Admin",
  email: "prototype@local.dev",
  googleId: "prototype-user",
};

const rewards = { stars: 5, xp: 15 };

function parseBody(options = {}) {
  if (!options.body) return {};
  if (typeof options.body === "string") {
    try {
      return JSON.parse(options.body);
    } catch {
      return {};
    }
  }
  return options.body;
}

function mockResponse(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const body = parseBody(options);

  if (path === "/auth/me") return { auth: true, user: PROTOTYPE_USER };
  if (path === "/auth/login" && method === "POST") return { token: "prototype-token", user: PROTOTYPE_USER };
  if (path === "/auth/register" && method === "POST") return { user: { ...PROTOTYPE_USER, ...body } };

  if (path === "/admin/ai/overview") {
    return {
      data: {
        totals: { motions: 24, voices: 11, journals: 8, avg_score: 92 },
        byType: [
          { metric_type: "motion", avg_score: 94, samples: 24 },
          { metric_type: "voice", avg_score: 89, samples: 11 },
          { metric_type: "journal", avg_score: 93, samples: 8 },
        ],
        models: [
          {
            model_name: "simba-brain",
            version: "prototype-1",
            created_at: new Date().toISOString(),
            parameters: { mode: "prototype" },
          },
        ],
      },
    };
  }

  if (path === "/admin/ai/members") {
    return {
      members: [
        {
          display_name: "Prototype Admin",
          email: PROTOTYPE_USER.email,
          avg_score: 92,
          total_metrics: 43,
          motions: 24,
          voices: 11,
          journals: 8,
        },
      ],
    };
  }

  if (path === "/admin/ai/profiles") {
    return {
      profiles: [
        {
          member_id: PROTOTYPE_USER.id,
          motion_avg: 94,
          voice_avg: 89,
          journal_avg: 93,
          consistency_score: 95,
          current_difficulty: "adaptive",
        },
      ],
    };
  }

  if (path === "/admin/holistic/overview") {
    return {
      holistic: [
        {
          member_id: PROTOTYPE_USER.id,
          physical_score: 94,
          mental_score: 90,
          linguistic_score: 88,
          cultural_score: 97,
          overall_health: 92,
        },
      ],
    };
  }

  if (path === "/admin/overview") {
    return {
      ok: true,
      stats: { members_total: 1, shares_total: 0, stars_total: 0, bd_total: 1200 },
      platformBreakdown: [],
      recentActivity: [],
      totals: { members: 1, active: 1 },
    };
  }
  if (path === "/admin/members") return { members: [PROTOTYPE_USER] };
  if (path === "/admin/shares") return { shares: [] };
  if (path === "/admin/reviews") return { reviews: [] };
  if (path === "/admin/activity-stream") return { activity: [] };

  if (path.startsWith("/ledger/balance/")) {
    return { member_id: decodeURIComponent(path.split("/").pop() || PROTOTYPE_USER.id), balance: 1200 };
  }
  if (path === "/ledger/balance") return { balance: 1200 };
  if (path === "/ledger/activity") return { activity: [] };
  if (path === "/ledger/star-transactions") return { transactions: [] };
  if (path === "/ledger/bd-transactions") return { transactions: [] };
  if (path === "/ledger/notifications") return { notifications: [] };
  if (path === "/ledger/share" && method === "POST") return { ok: true, share: body };
  if (path === "/ledger/review-video" && method === "POST") return { ok: true, review: body };

  if (path === "/pagt/vote" && method === "POST") {
    return { ok: true, vote_id: `vote-${Date.now()}`, ...body };
  }

  if (path === "/fitness/log" && method === "POST") return { ok: true, reward: rewards, log: body };
  if (path === "/study/journal" && method === "POST") return { ok: true, reward: rewards, journal: body };
  if (path === "/study/share" && method === "POST") return { ok: true, reward: rewards, share: body };
  if (path === "/language/practice" && method === "POST") return { ok: true, reward: rewards, practice: body };
  if (path === "/forms/submit" && method === "POST") return { ok: true, reward: rewards, form: body };
  if (path === "/ai/session" && method === "POST") return { ok: true, reward: rewards, session: body };

  if (path === "/member/overview") return { totals: { workouts: 3, streak: 5, stars: 20 } };
  if (path === "/member/activity") return { activity: [] };

  return null;
}

export async function api(path, options = {}) {
  const mocked = mockResponse(path, options);
  if (mocked) return mocked;

  const url = `${API_BASE_URL}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const res = await fetch(url, {
    ...options,
    credentials: "omit",
    headers,
  });

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const msg = typeof data === "string" ? data : data?.error || data?.detail || "Unknown server error";
    throw new Error(msg);
  }

  return data;
}

export const get = (path) => api(path);
export const post = (path, body) => api(path, { method: "POST", body: JSON.stringify(body) });
export const put = (path, body) => api(path, { method: "PUT", body: JSON.stringify(body) });
export const del = (path) => api(path, { method: "DELETE" });
