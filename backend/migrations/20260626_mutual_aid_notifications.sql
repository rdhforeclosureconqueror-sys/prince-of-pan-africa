-- Mutual Aid Phase 6 notification records only; no external email/SMS/push dispatch.
CREATE TABLE IF NOT EXISTS mutual_aid_notifications (
  id INTEGER PRIMARY KEY,
  request_id INTEGER,
  disbursement_id INTEGER,
  recipient_user_id INTEGER,
  actor_user_id INTEGER,
  audience VARCHAR(64) NOT NULL DEFAULT 'member',
  event_type VARCHAR(128) NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT '',
  message TEXT NOT NULL DEFAULT '',
  delivery_status VARCHAR(64) NOT NULL DEFAULT 'recorded_only',
  channels JSON NOT NULL DEFAULT '[]',
  payload JSON NOT NULL DEFAULT '{}',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_mutual_aid_notifications_request_id ON mutual_aid_notifications(request_id);
CREATE INDEX IF NOT EXISTS ix_mutual_aid_notifications_recipient_user_id ON mutual_aid_notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS ix_mutual_aid_notifications_event_type ON mutual_aid_notifications(event_type);
CREATE INDEX IF NOT EXISTS ix_mutual_aid_notifications_audience ON mutual_aid_notifications(audience);
CREATE INDEX IF NOT EXISTS ix_mutual_aid_notifications_delivery_status ON mutual_aid_notifications(delivery_status);
