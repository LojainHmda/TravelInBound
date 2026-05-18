-- Per-day guide supplier selections on itinerary (JSON array of supplier IDs)
ALTER TABLE itinerary_row ADD COLUMN itinerary_guide_supplier_ids TEXT;
