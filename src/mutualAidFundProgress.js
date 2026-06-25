import {
  MUTUAL_AID_ACTIVATION_THRESHOLD,
  MUTUAL_AID_CURRENT_PROGRESS,
  MUTUAL_AID_STATUS,
} from "./config";

export { MUTUAL_AID_ACTIVATION_THRESHOLD, MUTUAL_AID_CURRENT_PROGRESS, MUTUAL_AID_STATUS };

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const activationRequirements = [
  "approved policy",
  "governance process",
  "accounting controls",
  "privacy rules",
  "approval controls",
  "trained committee",
  "legal/tax/compliance review before public launch",
];

export function formatMutualAidCurrency(value) {
  return currencyFormatter.format(value);
}

export function getMutualAidFundProgress() {
  const threshold = MUTUAL_AID_ACTIVATION_THRESHOLD;
  const current = MUTUAL_AID_CURRENT_PROGRESS;
  const remaining = Math.max(threshold - current, 0);
  const percentage = threshold > 0 ? Math.min(100, Math.round((current / threshold) * 100)) : 0;

  return {
    threshold,
    current,
    remaining,
    percentage,
    status: MUTUAL_AID_STATUS,
  };
}
