import { api } from "../api/api";

async function request(path, opts = {}) {
  return api(path, opts);
}

export const ledgerV2Api = {
  me: () => request("/auth/me"),
  balance: () => request("/ledger/balance"),
  share: (payload) =>
    request("/ledger/share", { method: "POST", body: JSON.stringify(payload) }),
  reviewVideo: (payload) =>
    request("/ledger/review-video", { method: "POST", body: JSON.stringify(payload) }),
};
