import { API_BASE } from "../config";

async function request(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });

  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const msg =
      typeof data === "string"
        ? data
        : data?.error || data?.message || "Request failed";
    throw new Error(msg);
  }

  return data;
}

export const ledgerV2Api = {
  me: () => request("/auth/me"),
  balance: () => request("/ledger/balance"),
  share: (payload) =>
    request("/ledger/share", { method: "POST", body: JSON.stringify(payload) }),
  reviewVideo: (payload) =>
    request("/ledger/review-video", { method: "POST", body: JSON.stringify(payload) }),
};
