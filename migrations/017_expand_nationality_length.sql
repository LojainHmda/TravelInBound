-- Expand inbound_request.nationality for mixed-nationality strings, e.g. "British (3), American (2)"
-- PostgreSQL
ALTER TABLE inbound_request ALTER COLUMN nationality TYPE VARCHAR(500);
