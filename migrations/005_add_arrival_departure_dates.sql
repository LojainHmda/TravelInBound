-- Migration: Add arrival_date and departure_date to arrival_departure table
-- Date: 2025-11-04
-- Description: Adds date columns to map arrivals/departures to specific itinerary days

ALTER TABLE arrival_departure 
ADD COLUMN IF NOT EXISTS arrival_date DATE,
ADD COLUMN IF NOT EXISTS departure_date DATE;

-- Note: These dates link to itinerary_row dates for auto-flagging with flag_airport
