# AI Chat to Database Mapping Logic

## How It Works Step-by-Step:

### 1. User Input Processing
```
User types: "Find customer Dalia"
```

### 2. OpenAI Intent Analysis
The AI service sends this prompt to OpenAI:
```python
system_prompt = """
You are an AI assistant for a travel booking platform. Analyze the user's query and extract:
1. Intent (search_booking, customer_info, etc.)
2. Entities (booking reference, customer name, dates, etc.)

Respond with JSON format:
{
    "intent": "search_customer",
    "entities": {
        "customer_name": "Dalia"
    },
    "confidence": 0.9
}
"""
```

### 3. Database Query Generation
Based on the extracted entities, the system builds real SQL queries:

```python
# For customer search:
if entities.get("customer_name"):
    name = entities["customer_name"]  # "Dalia"
    
    # Creates this SQL query:
    SELECT * FROM customer 
    WHERE first_name ILIKE '%Dalia%' 
    OR last_name ILIKE '%Dalia%' 
    OR company_name ILIKE '%Dalia%'
    LIMIT 15;

# For booking search:
if entities.get("booking_reference"):
    ref = entities["booking_reference"]  # "IR-123"
    
    # Creates this SQL query:
    SELECT * FROM booking 
    WHERE reference_number ILIKE '%IR-123%'
    LIMIT 10;
```

### 4. Real Data Retrieval
The system executes these queries against your PostgreSQL database and gets actual results:

```python
# Example result for Dalia search:
customers = [
    {
        "id": 15,
        "name": "Dalia Johnson",
        "email": "dalia@email.com",
        "phone": "+1234567890",
        "customer_type": "Individual"
    }
]
```

### 5. AI Response Generation
The real data is sent back to OpenAI with context:

```python
system_prompt = f"""
User Query: "Find customer Dalia"
Available Customer Data: {json.dumps(customers)}

Instructions:
1. Provide a helpful, conversational response
2. Include relevant customer information when available
3. Use a friendly, professional tone
"""
```

### 6. Final Response
OpenAI generates a natural language response:
```
"I found Dalia Johnson in your customer database! Here are her details:
• Name: Dalia Johnson
• Email: dalia@email.com
• Phone: +1234567890
• Customer Type: Individual

Would you like to see her booking history or update her information?"
```

## Key Technical Components:

### Entity Extraction Mapping:
- **Customer names** → `Customer.first_name`, `Customer.last_name`
- **Booking references** → `Booking.reference_number`
- **Destinations** → `ServiceItem.description`
- **Dates** → `Booking.created_at`, `ServiceItem.start_date`

### Database Tables Used:
- `customer` - Customer information
- `booking` - Booking records
- `service_item` - Travel services
- `payment` - Payment records
- `supplier_payment` - Supplier costs

### Fuzzy Search Logic:
```sql
-- For "Dalia" search, generates:
WHERE (
    first_name ILIKE '%Dalia%' OR
    last_name ILIKE '%Dalia%' OR
    company_name ILIKE '%Dalia%'
)

-- Case insensitive and partial matching
-- Finds: "Dalia", "DALIA", "Dalia Smith", "Company Dalia Inc"
```

## Data Flow Summary:
```
Natural Language → OpenAI Analysis → SQL Queries → Real Database → Results → AI Processing → Natural Response
```

The system never uses fake data - everything comes from your actual PostgreSQL database!