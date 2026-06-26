-- Mutual Aid member request intake metadata only.
-- Guardrail: no payments, payouts, wallets, reimbursements, approvals, or disbursement logic.

ALTER TABLE mutual_aid_requests ADD COLUMN IF NOT EXISTS urgency VARCHAR(64) NOT NULL DEFAULT 'standard';
ALTER TABLE mutual_aid_requests ADD COLUMN IF NOT EXISTS preferred_support_method VARCHAR(128) NOT NULL DEFAULT 'community_follow_up';
ALTER TABLE mutual_aid_requests ADD COLUMN IF NOT EXISTS policy_consent BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE mutual_aid_requests ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP NULL;

ALTER TABLE mutual_aid_request_documents ADD COLUMN IF NOT EXISTS filename VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE mutual_aid_request_documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE mutual_aid_request_documents ADD COLUMN IF NOT EXISTS file_size INTEGER NOT NULL DEFAULT 0;
