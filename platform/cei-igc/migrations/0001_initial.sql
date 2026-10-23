-- DRAFTS ONLY. Holdout contents NEVER belong in this database.
CREATE TABLE IF NOT EXISTS investigations (
  case_id TEXT PRIMARY KEY,
  owner_sub TEXT NOT NULL,
  intake_json TEXT NOT NULL,
  arena_json TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_investigations_owner ON investigations(owner_sub,updated_at);
CREATE TABLE IF NOT EXISTS arena_jobs (
  job_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  owner_sub TEXT NOT NULL,
  snapshot_key TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL,
  case_version INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('DISPATCHING','QUEUED','RUNNING','COMPLETE','ERROR','DISPATCH_ERROR')),
  github_run_id TEXT,
  github_url TEXT,
  result_key TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(case_id) REFERENCES investigations(case_id)
);
CREATE INDEX IF NOT EXISTS ix_arena_jobs_case ON arena_jobs(case_id,created_at);

