-- Initial database setup script
-- This will be run when the PostgreSQL container first starts

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can add initial data here

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes that might be useful for performance
-- These will be created after the tables are created by Alembic

-- Sample locations data (will be inserted after tables are created)
-- This data can be loaded via the API or a separate data migration