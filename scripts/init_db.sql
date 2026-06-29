-- scripts/init_db.sql
-- Runs once when PostgreSQL container first starts
-- Sets up extensions needed by CineAI

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Better text search (optional, for future full-text search features)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Better JSON operations
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Performance settings (applied to this session, override in postgresql.conf for permanent)
-- These are good defaults for a 1-2GB RAM instance

COMMENT ON DATABASE cineai IS 'CineAI — AI-powered movie recommendation platform';
