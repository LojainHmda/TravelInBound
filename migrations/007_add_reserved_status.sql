-- Migration 007: Add RESERVED status support for service line items
-- This allows tracking individual supplier confirmations before overall booking confirmation

-- The status column already exists and accepts string values
-- This migration is informational only - no schema changes needed
-- RESERVED status is now available for InboundHotel and InboundTransport

-- Status workflow for service line items:
-- REQUEST -> QUOTED -> RESERVED (Supplier Confirmed) -> CONFIRMED

-- When ALL service items are RESERVED, the InboundRequest can move to CONFIRMED

SELECT 'Migration 007: RESERVED status support added' AS message;
