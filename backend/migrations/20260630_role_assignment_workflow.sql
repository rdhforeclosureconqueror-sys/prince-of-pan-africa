CREATE TABLE IF NOT EXISTS society_role_openings (
    id INTEGER PRIMARY KEY,
    society_id INTEGER NOT NULL REFERENCES societies(id),
    title VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL DEFAULT '',
    responsibilities JSON NOT NULL DEFAULT '[]',
    required_behaviors JSON NOT NULL DEFAULT '[]',
    handbook_chapters JSON NOT NULL DEFAULT '[]',
    recommended_assessments JSON NOT NULL DEFAULT '[]',
    status VARCHAR(64) NOT NULL DEFAULT 'open',
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_role_openings_society_id ON society_role_openings(society_id);
CREATE INDEX IF NOT EXISTS ix_society_role_openings_status ON society_role_openings(status);

CREATE TABLE IF NOT EXISTS society_role_candidate_reviews (
    id INTEGER PRIMARY KEY,
    society_id INTEGER NOT NULL REFERENCES societies(id),
    role_opening_id INTEGER NOT NULL REFERENCES society_role_openings(id),
    candidate_member_id INTEGER NOT NULL REFERENCES society_first_ten_members(id),
    alignment_label VARCHAR(64) NOT NULL DEFAULT 'Emerging Alignment',
    behavioral_confidence VARCHAR(128) NOT NULL DEFAULT 'Limited evidence',
    behavioral_evidence JSON NOT NULL DEFAULT '[]',
    assessment_evidence JSON NOT NULL DEFAULT '[]',
    growth_path JSON NOT NULL DEFAULT '[]',
    missing_assessments JSON NOT NULL DEFAULT '[]',
    current_strengths JSON NOT NULL DEFAULT '[]',
    handbook_references JSON NOT NULL DEFAULT '[]',
    complementary_teammates JSON NOT NULL DEFAULT '[]',
    reviewer_notes TEXT NOT NULL DEFAULT '',
    decision VARCHAR(64) NOT NULL DEFAULT 'community_review',
    development_plan JSON NOT NULL DEFAULT '{}',
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_role_candidate_review UNIQUE (role_opening_id, candidate_member_id)
);
CREATE INDEX IF NOT EXISTS ix_society_role_candidate_reviews_society_id ON society_role_candidate_reviews(society_id);
CREATE INDEX IF NOT EXISTS ix_society_role_candidate_reviews_decision ON society_role_candidate_reviews(decision);

CREATE TABLE IF NOT EXISTS society_role_discussion_notes (
    id INTEGER PRIMARY KEY,
    society_id INTEGER NOT NULL REFERENCES societies(id),
    role_opening_id INTEGER NOT NULL REFERENCES society_role_openings(id),
    candidate_review_id INTEGER REFERENCES society_role_candidate_reviews(id),
    note TEXT NOT NULL DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_role_discussion_notes_society_id ON society_role_discussion_notes(society_id);

CREATE TABLE IF NOT EXISTS society_role_appointment_history (
    id INTEGER PRIMARY KEY,
    society_id INTEGER NOT NULL REFERENCES societies(id),
    role_opening_id INTEGER NOT NULL REFERENCES society_role_openings(id),
    candidate_member_id INTEGER NOT NULL REFERENCES society_first_ten_members(id),
    role_title VARCHAR(255) NOT NULL DEFAULT '',
    start_date DATE,
    reason TEXT NOT NULL DEFAULT '',
    supporting_evidence JSON NOT NULL DEFAULT '[]',
    community_notes JSON NOT NULL DEFAULT '[]',
    review_date DATE,
    mentor VARCHAR(255) NOT NULL DEFAULT '',
    training_status VARCHAR(128) NOT NULL DEFAULT 'Not started',
    successor VARCHAR(255) NOT NULL DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_role_appointment_history_society_id ON society_role_appointment_history(society_id);
CREATE INDEX IF NOT EXISTS ix_society_role_appointment_history_review_date ON society_role_appointment_history(review_date);
