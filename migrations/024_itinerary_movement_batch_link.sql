-- Link ItineraryRow movement rows back to the ArrivalBatch / DepartureBatch
-- they were generated from, so deleting a batch keeps the Itinerary in sync.
-- SQLite / PostgreSQL compatible (adjust if your DB already has the columns).
--
-- NOTE: backfilling existing movement rows (matching them to batches by date)
-- requires procedural logic and is handled by the companion applier:
--   scripts/migrations/add_itinerary_movement_batch_link.py
-- Run that script rather than this file to also backfill existing data.

ALTER TABLE itinerary_row ADD COLUMN source_arrival_batch_id INTEGER REFERENCES arrival_batch(id);
ALTER TABLE itinerary_row ADD COLUMN source_departure_batch_id INTEGER REFERENCES departure_batch(id);
