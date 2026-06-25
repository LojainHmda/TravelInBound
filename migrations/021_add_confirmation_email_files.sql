-- Add confirmation email file support to hotel, transport, and meal services

-- Add columns to inbound_hotel table
ALTER TABLE inbound_hotel ADD COLUMN IF NOT EXISTS confirmation_email_filename VARCHAR(255) NULL;
ALTER TABLE inbound_hotel ADD COLUMN IF NOT EXISTS confirmation_email_filepath VARCHAR(500) NULL;
ALTER TABLE inbound_hotel ADD COLUMN IF NOT EXISTS confirmation_email_uploaded_at TIMESTAMP NULL;

-- Add columns to inbound_transport table
ALTER TABLE inbound_transport ADD COLUMN IF NOT EXISTS confirmation_email_filename VARCHAR(255) NULL;
ALTER TABLE inbound_transport ADD COLUMN IF NOT EXISTS confirmation_email_filepath VARCHAR(500) NULL;
ALTER TABLE inbound_transport ADD COLUMN IF NOT EXISTS confirmation_email_uploaded_at TIMESTAMP NULL;

-- Add columns to inbound_meal table
ALTER TABLE inbound_meal ADD COLUMN IF NOT EXISTS confirmation_email_filename VARCHAR(255) NULL;
ALTER TABLE inbound_meal ADD COLUMN IF NOT EXISTS confirmation_email_filepath VARCHAR(500) NULL;
ALTER TABLE inbound_meal ADD COLUMN IF NOT EXISTS confirmation_email_uploaded_at TIMESTAMP NULL;
