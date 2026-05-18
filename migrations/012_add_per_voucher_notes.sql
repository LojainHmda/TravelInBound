-- Add per-voucher note columns to inbound_request (restaurant and hotel vouchers isolated)
-- Run once; SQLite does not support IF NOT EXISTS for ADD COLUMN
ALTER TABLE inbound_request ADD COLUMN restaurant_voucher_note TEXT;
ALTER TABLE inbound_request ADD COLUMN hotel_voucher_note TEXT;
