-- Mutual Aid Phase 4 decision workflow metadata only.
-- No payments, payouts, wallets, reimbursements, or disbursement execution are added.
ALTER TABLE mutual_aid_decisions ADD COLUMN reason_code VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE mutual_aid_decisions ADD COLUMN appeal_eligible BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE mutual_aid_decisions ADD COLUMN appeal_deadline TIMESTAMP NULL;
ALTER TABLE mutual_aid_decisions ADD COLUMN appeal_instructions TEXT NOT NULL DEFAULT '';
