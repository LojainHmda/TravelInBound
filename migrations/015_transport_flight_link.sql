-- Link InboundTransport stubs to ArrivalBatch / DepartureBatch; optional needs_transport on batches.
-- SQLite / PostgreSQL compatible (adjust if your DB already has columns).

ALTER TABLE arrival_batch ADD COLUMN needs_transport BOOLEAN DEFAULT 1;
ALTER TABLE departure_batch ADD COLUMN needs_transport BOOLEAN DEFAULT 1;
ALTER TABLE inbound_transport ADD COLUMN source_arrival_batch_id INTEGER REFERENCES arrival_batch(id);
ALTER TABLE inbound_transport ADD COLUMN source_departure_batch_id INTEGER REFERENCES departure_batch(id);
