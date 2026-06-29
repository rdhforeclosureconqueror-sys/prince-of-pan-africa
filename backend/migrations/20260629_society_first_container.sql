-- Society Container Registry foundation for the First Container / 100-Day Formation Container only.
-- Future containers (90-Day, Institution, Ecosystem, Wealth, Property, Federation, Legacy) are intentionally not installed here.
CREATE TABLE IF NOT EXISTS society_containers (
  id SERIAL PRIMARY KEY,
  society_id INTEGER NOT NULL,
  container_type VARCHAR(128) NOT NULL DEFAULT 'first_container_100_day',
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status VARCHAR(64) NOT NULL DEFAULT 'draft',
  start_date DATE,
  target_end_date DATE,
  current_day INTEGER NOT NULL DEFAULT 1,
  current_week INTEGER NOT NULL DEFAULT 1,
  percent_complete INTEGER NOT NULL DEFAULT 0,
  active_milestone_id INTEGER,
  source_guide VARCHAR(255) NOT NULL DEFAULT 'Mutual Aid Society Handbook / First 100 Days Container',
  created_by INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_containers_society_id ON society_containers (society_id);
CREATE INDEX IF NOT EXISTS ix_society_containers_container_type ON society_containers (container_type);
CREATE INDEX IF NOT EXISTS ix_society_containers_status ON society_containers (status);

CREATE TABLE IF NOT EXISTS society_container_milestones (
  id SERIAL PRIMARY KEY,
  container_id INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sequence_order INTEGER NOT NULL DEFAULT 0,
  phase_label VARCHAR(128) NOT NULL DEFAULT '',
  percent_weight INTEGER NOT NULL DEFAULT 0,
  status VARCHAR(64) NOT NULL DEFAULT 'not_started',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_container_milestones_container_id ON society_container_milestones (container_id);
CREATE INDEX IF NOT EXISTS ix_society_container_milestones_sequence_order ON society_container_milestones (sequence_order);
CREATE INDEX IF NOT EXISTS ix_society_container_milestones_status ON society_container_milestones (status);

CREATE TABLE IF NOT EXISTS society_trust_tasks (
  id SERIAL PRIMARY KEY,
  society_id INTEGER NOT NULL,
  container_id INTEGER NOT NULL,
  milestone_id INTEGER,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status VARCHAR(64) NOT NULL DEFAULT 'backlog',
  lane VARCHAR(64) NOT NULL DEFAULT 'systems',
  task_type VARCHAR(128) NOT NULL DEFAULT 'container_step',
  owner_member_id INTEGER,
  linked_role VARCHAR(128) NOT NULL DEFAULT '',
  linked_module VARCHAR(128) NOT NULL DEFAULT '',
  linked_handbook_chapter VARCHAR(128) NOT NULL DEFAULT '',
  source_book_slug VARCHAR(255) NOT NULL DEFAULT '',
  source_book_id INTEGER,
  source_section_id INTEGER,
  source_chapter_slug VARCHAR(255) NOT NULL DEFAULT '',
  source_chapter_label VARCHAR(128) NOT NULL DEFAULT '',
  source_reader_path TEXT NOT NULL DEFAULT '',
  source_reference_type VARCHAR(64) NOT NULL DEFAULT '',
  linked_container_step VARCHAR(128) NOT NULL DEFAULT '',
  due_date DATE,
  priority VARCHAR(64) NOT NULL DEFAULT 'normal',
  blocked_reason TEXT NOT NULL DEFAULT '',
  completion_notes TEXT NOT NULL DEFAULT '',
  created_from_template BOOLEAN NOT NULL DEFAULT TRUE,
  created_by INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_society_trust_tasks_society_id ON society_trust_tasks (society_id);
CREATE INDEX IF NOT EXISTS ix_society_trust_tasks_container_id ON society_trust_tasks (container_id);
CREATE INDEX IF NOT EXISTS ix_society_trust_tasks_milestone_id ON society_trust_tasks (milestone_id);
CREATE INDEX IF NOT EXISTS ix_society_trust_tasks_status ON society_trust_tasks (status);
CREATE INDEX IF NOT EXISTS ix_society_trust_tasks_lane ON society_trust_tasks (lane);
