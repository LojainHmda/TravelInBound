-- Add "Attach Visa" file support to the arrival batch.
-- Reuses the shared confirmation-email upload mechanism internally, so the
-- column names mirror the existing hotel/transport/meal confirmation columns.

ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS confirmation_email_filename VARCHAR(255) NULL;
ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS confirmation_email_filepath VARCHAR(500) NULL;
ALTER TABLE arrival_batch ADD COLUMN IF NOT EXISTS confirmation_email_uploaded_at TIMESTAMP NULL;
