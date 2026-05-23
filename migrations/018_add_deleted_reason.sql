-- Reason entered when a request is moved to the Deleted queue
ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS deleted_reason TEXT;
