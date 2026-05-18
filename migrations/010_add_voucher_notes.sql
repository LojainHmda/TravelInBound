-- Add voucher_notes column to inbound_hotel (notes specific to voucher, separate from hotel notes)
ALTER TABLE inbound_hotel ADD COLUMN IF NOT EXISTS voucher_notes TEXT;
