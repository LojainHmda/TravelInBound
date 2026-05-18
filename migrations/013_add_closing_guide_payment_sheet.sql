-- Add closing guide payment sheet data column (isolated from advance expense sheet)
-- Run once; SQLite does not support IF NOT EXISTS for ADD COLUMN
ALTER TABLE inbound_request ADD COLUMN closing_guide_payment_sheet_data TEXT;
