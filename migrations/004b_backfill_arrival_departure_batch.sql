-- Migration: Backfill legacy arrival/departure data into new batch fields
-- Date: 2025-11-04
-- Description: Converts existing ARRIVAL/DEPARTURE records into the new batch structure
--              to prevent data loss

-- Step 1: Backfill ARRIVAL records into new arrival_* fields
UPDATE arrival_departure 
SET 
    arrival_point = point,
    arrival_time = time,
    arrival_driver_name = driver_name
WHERE type = 'ARRIVAL' 
  AND (arrival_point IS NULL OR arrival_time IS NULL);

-- Step 2: Backfill DEPARTURE records into new departure_* fields
UPDATE arrival_departure 
SET 
    departure_point = point,
    departure_time = time
WHERE type = 'DEPARTURE' 
  AND (departure_point IS NULL OR departure_time IS NULL);

-- Note: For paired batch records, both arrival and departure fields 
-- should be filled in the UI. This migration only handles legacy single-type records.
