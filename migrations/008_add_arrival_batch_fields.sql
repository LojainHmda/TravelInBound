-- Add meet_assist and representative_name fields to arrival_batch table
ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS meet_assist BOOLEAN DEFAULT FALSE;
ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS representative_name VARCHAR(200);
