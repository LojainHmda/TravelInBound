-- Add bank_iban field to supplier table
ALTER TABLE supplier ADD COLUMN bank_iban VARCHAR(100) DEFAULT NULL;
