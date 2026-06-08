-- Add entity_type column to supplier table to distinguish between Company and Freelancer
ALTER TABLE supplier ADD COLUMN entity_type VARCHAR(20) DEFAULT 'COMPANY';

-- Add payment_method column for storing the payment method (used for freelancers and others)
ALTER TABLE supplier ADD COLUMN payment_method VARCHAR(50);
