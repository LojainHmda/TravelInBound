-- Migration 006: Quotation System
-- Adds quotation workflow to inbound tour operator system
-- Flow: REQUEST → QUOTED → CONFIRMED → PROCESSING

-- Create inbound_quotation table
CREATE TABLE IF NOT EXISTS inbound_quotation (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES inbound_request(id) ON DELETE CASCADE,
    
    -- Quotation metadata
    quotation_number VARCHAR(50) UNIQUE NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'DRAFT',
    
    -- Quotation details
    valid_until DATE,
    notes TEXT,
    subtotal NUMERIC(12, 2) DEFAULT 0.00,
    tax_rate NUMERIC(5, 2) DEFAULT 0.00,
    tax_amount NUMERIC(12, 2) DEFAULT 0.00,
    total_amount NUMERIC(12, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Tracking
    created_by INTEGER NOT NULL REFERENCES "user"(id),
    sent_at TIMESTAMP,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create inbound_quotation_item table
CREATE TABLE IF NOT EXISTS inbound_quotation_item (
    id SERIAL PRIMARY KEY,
    quotation_id INTEGER NOT NULL REFERENCES inbound_quotation(id) ON DELETE CASCADE,
    
    -- Line item details
    item_order INTEGER DEFAULT 0,
    description TEXT NOT NULL,
    quantity NUMERIC(10, 2) DEFAULT 1.00,
    unit_price NUMERIC(12, 2) DEFAULT 0.00,
    line_total NUMERIC(12, 2) DEFAULT 0.00,
    
    -- Optional categorization
    category VARCHAR(50),
    notes TEXT,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quotation_attachment table
CREATE TABLE IF NOT EXISTS quotation_attachment (
    id SERIAL PRIMARY KEY,
    quotation_id INTEGER NOT NULL REFERENCES inbound_quotation(id) ON DELETE CASCADE,
    
    -- File details
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Metadata
    description TEXT,
    uploaded_by INTEGER NOT NULL REFERENCES "user"(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add unique constraint for version control
ALTER TABLE inbound_quotation 
ADD CONSTRAINT uq_request_version UNIQUE (request_id, version);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_quotation_request ON inbound_quotation(request_id);
CREATE INDEX IF NOT EXISTS idx_quotation_number ON inbound_quotation(quotation_number);
CREATE INDEX IF NOT EXISTS idx_quotation_item_quotation ON inbound_quotation_item(quotation_id);
CREATE INDEX IF NOT EXISTS idx_quotation_attachment_quotation ON quotation_attachment(quotation_id);
