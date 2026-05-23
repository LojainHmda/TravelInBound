-- Linked attachment: child inbound requests linked to a main file
ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS parent_request_id INTEGER REFERENCES inbound_request(id);
ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS link_type VARCHAR(20);
ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS link_note TEXT;
