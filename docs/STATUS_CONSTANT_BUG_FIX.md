# Critical Bug Fix: Status Constant Mismatch in Service Items

## Problem

When creating new service requests (guides, hotels, transport), the Rundown analytics page showed **0 Requested** for those newly created items, even though they were clearly in "Requested" status.

**Example:** Created a request with guide "Heba" in Requested status → Analytics showed 0 Requested guides

## Root Cause

There was a **status constant mismatch** between:
- **Data layer (where services are saved):** Using `'REQUESTED'` (9 characters)
- **Query layer (where analytics aggregates):** Looking for `'REQUEST'` (7 characters)

### How It Happened

**When saving guides, hotels, and transport:**
```python
# app/routes/inbound.py line 2691, 2855, 2998, etc.
guide.status = form_data.get('guide_status', 'REQUESTED')  # ← Wrong!
hotel.status = form_data.get('hotel_status', 'REQUESTED')  # ← Wrong!
transport.status = form_data.get('transport_status', 'REQUESTED')  # ← Wrong!
```

**When aggregating in analytics:**
```python
# app/routes/inbound.py line 10113
func.sum(_when(InboundGuide.status, 'REQUEST')).label('requested'),  # ← Looking for 'REQUEST'
```

**Result:** New guides saved with status='REQUESTED' never matched the query filter for status='REQUEST', so they were never counted.

## Solution

Changed all three service types to use the correct constant `'REQUEST'`:

### Files Modified

**app/routes/inbound.py** — Four changes in the guide/hotel/transport save handlers:

1. **Line 2691** — Hotel status default
   - Before: `'REQUESTED'`
   - After: `'REQUEST'`

2. **Line 2855** — Transport status default
   - Before: `'REQUESTED'`
   - After: `'REQUEST'`

3. **Line 2998** — Guide status default (itinerary-linked)
   - Before: `'REQUESTED'`
   - After: `'REQUEST'`

4. **Line 3040** — Guide status default (standalone)
   - Before: `'REQUESTED'`
   - After: `'REQUEST'`

## Verification

Now all services use the standard status constants:
- `STATUS_REQUEST = 'REQUEST'` (defined in app/models/__init__.py:11)
- `STATUS_CONFIRMED = 'CONFIRMED'`
- `STATUS_INVOICED = 'INVOICED'`

The analytics aggregation queries correctly match services by their status:
```python
func.sum(_when(InboundGuide.status, 'REQUEST')).label('requested'),
func.sum(_when(InboundGuide.status, 'CONFIRMED')).label('confirmed'),
func.sum(_when(InboundGuide.status, 'INVOICED')).label('invoiced'),
```

## Testing

**Before fix:**
```
Create guide "Heba" with status "Requested"
→ Guide saved as status='REQUESTED'
→ Analytics query looks for status='REQUEST'
→ No match: Shows 0 Requested guides
```

**After fix:**
```
Create guide "Heba" with status "Requested"
→ Guide saved as status='REQUEST' ✓
→ Analytics query looks for status='REQUEST' ✓
→ Match found: Shows 1 Requested guide ✓
```

To verify:
1. Create a new request with a guide/hotel/transport
2. Open Rundown Analytics
3. Check the "Requested" count for that supplier
4. Should now show the correct count

## Related Issues

This bug also affected:
- Hotel booking analytics (Hotels tab showing 0 requested)
- Transport booking analytics (Transportation tab showing 0 requested)
- Any newly created service items in the Rundown page

All are now fixed by this single change.

## Architecture Note

The root issue: service creation code wasn't using the status constants imported from `app/models/__init__.py`. Instead, it had hardcoded string defaults that didn't match the canonical values.

**Lesson:** Always use imported constants for enumerated values — don't hardcode strings that might diverge from the source of truth.
