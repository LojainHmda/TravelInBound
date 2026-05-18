-- Add voucher_notes column to inbound_meal (notes specific to restaurant voucher, editable and saved per restaurant)
-- Note: SQLite does not support IF NOT EXISTS for ADD COLUMN; run once only
ALTER TABLE inbound_meal ADD COLUMN voucher_notes TEXT;
