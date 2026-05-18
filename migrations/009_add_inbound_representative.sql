-- Create inbound_representative table for dropdown lookup
CREATE TABLE IF NOT EXISTS inbound_representative (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add unique constraint on name to avoid duplicates
CREATE UNIQUE INDEX IF NOT EXISTS ix_inbound_representative_name ON inbound_representative (name);
