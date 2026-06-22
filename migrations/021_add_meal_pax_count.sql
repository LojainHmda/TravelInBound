-- Add PAX count column to inbound_meal table
-- This allows restaurant PAX to be independent from the main request PAX
-- Example: Request has 5 travelers but restaurant meal is for 10 guests (including local guests)

ALTER TABLE inbound_meal ADD COLUMN pax_count INT NULL;

-- Add index for better query performance if needed
-- (Optional, uncomment if filtering by pax_count becomes common)
-- CREATE INDEX idx_inbound_meal_pax_count ON inbound_meal(pax_count);
