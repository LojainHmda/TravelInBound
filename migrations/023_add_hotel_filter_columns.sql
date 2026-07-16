-- Remember the Hotel form's City / Category filter selections per request so
-- they are restored when the request is reopened (any status). These are
-- UI-only filters for the Hotel Name dropdown and do not change any stored
-- hotel record.

ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS hotel_filter_city VARCHAR(150) NULL;
ALTER TABLE inbound_request ADD COLUMN IF NOT EXISTS hotel_filter_category VARCHAR(100) NULL;
