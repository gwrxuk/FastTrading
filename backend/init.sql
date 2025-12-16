-- FastTrading Database Initialization
-- This script runs on first database creation

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (if tables exist)
-- These will be created by SQLAlchemy migrations

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE fasttrading TO trading;

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Tables will be created by the FastAPI application on startup
-- using SQLAlchemy's create_all() method

