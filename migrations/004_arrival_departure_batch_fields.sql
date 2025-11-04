-- Migration: Add batch-based fields to arrival_departure table
-- Date: 2025-11-04
-- Description: Extends arrival_departure table to support batch-based arrivals/departures
--              where each record contains both arrival and departure information for a group

-- Add new batch identification fields
ALTER TABLE arrival_departure 
ADD COLUMN IF NOT EXISTS batch_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS pax_count INTEGER;

-- Add arrival detail fields
ALTER TABLE arrival_departure 
ADD COLUMN IF NOT EXISTS arrival_point VARCHAR(150),
ADD COLUMN IF NOT EXISTS arrival_time TIME,
ADD COLUMN IF NOT EXISTS arrival_driver_name VARCHAR(200);

-- Add departure detail fields
ALTER TABLE arrival_departure 
ADD COLUMN IF NOT EXISTS departure_point VARCHAR(150),
ADD COLUMN IF NOT EXISTS departure_time TIME;

-- Make existing required columns nullable for batch-based approach
-- This allows for backwards compatibility and flexible usage
ALTER TABLE arrival_departure 
ALTER COLUMN type DROP NOT NULL,
ALTER COLUMN date DROP NOT NULL,
ALTER COLUMN point DROP NOT NULL;

-- Note: visa_type, meeting_assistance, and departure_tax columns already exist
-- from previous migrations and are used in the batch structure
