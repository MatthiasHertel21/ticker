-- Ticker Database Initialization
-- This script runs automatically when the PostgreSQL container starts

-- Create database if not exists (handled by POSTGRES_DB env var)

-- Enable UUID extension for better IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create initial admin user (if needed later)
-- This will be handled by Flask migrations instead
