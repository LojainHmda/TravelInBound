# Single Source of Truth: Supplier Analytics Data Consistency Fix

## Problem

The Rundown analytics page showed inconsistent data when switching between status tabs (Requested, Confirmed, Invoiced). 

**Example:** If an order had 3 guides in "Requested" status, switching to "Confirmed" would show different counts, as if the guides were being re-calculated per status rather than maintained as a single truth.

### Root Cause

The `supplier_analytics_api()` endpoint was applying the selected status as a **base query filter**, not just a presentation filter:

```python
# BEFORE (BROKEN)
sf = _status_filter(InboundGuide.status)  
if sf is not None:
    base_filters.append(sf)  # ← Restricts the entire dataset!
```

This meant:
- If user selected "Confirmed" tab, query returned ONLY confirmed records
- Conditional aggregation then tried to count statuses within that already-filtered set
- Result: impossible combinations (e.g., count of INVOICED records among CONFIRMED-only rows = 0)

## Solution

**Separated concerns:**
1. **Data layer** — always aggregates on the full dataset (all statuses)
2. **Presentation layer** — status tabs control UI highlighting, not data fetching

### Code Changes

In `app/routes/inbound.py`, the `supplier_analytics_api()` endpoint:

1. **Removed status-based query filtering**
   - Deleted the `_status_filter()` helper function
   - Removed `base_filters.append(sf)` logic from GUIDE, TRANSPORT, RESTAURANT, HOTEL sections
   - Base query now only filters by **date range and supplier type**

2. **Preserved conditional aggregation**
   - Queries still count CONFIRMED, REQUESTED, INVOICED separately
   - But now they run on the FULL dataset, not a pre-filtered subset
   - Counts reflect true distribution regardless of selected tab

3. **Used status parameter for UI only**
   - `statuses` still returned in JSON response
   - Frontend uses it to highlight/sort columns
   - Does NOT filter the data being fetched

### Example Behavior

**Before:** Clicking "Confirmed" tab
```
Request | Guide A | Guide B | Guide C
─────────────────────────────────────
Total      3        -         -
Confirmed  3        -         -
Requested  0        -         -  ← Wrong! (should show cross-tab counts)
Invoiced   0        -         -
```

**After:** Clicking any status tab
```
Request | Guide A | Guide B | Guide C  (same data regardless of tab)
─────────────────────────────────────
Total      3        2        1
Confirmed  2        1        1
Requested  1        1        0
Invoiced   0        0        0   ← Correct totals across all statuses
```

## Files Modified

- `app/routes/inbound.py` — `supplier_analytics_api()` function (lines 10068–10513)

## Testing the Fix

1. Open the Rundown Analytics page
2. View Guides/Hotels/Transport/Restaurants with multiple status records
3. Click between "Requested", "Confirmed", and "Invoiced" tabs
4. **Expected:** The "Total" and per-item counts remain consistent; only the highlighted column changes
5. **Before fix:** Totals would change per tab (indicating data was being re-queried filtered)

## Architecture Principles

This fix enforces these principles going forward:

- ✅ **Single source of truth:** One order = consistent data across all views
- ✅ **Status tabs are views:** They highlight/sort, they don't filter the base dataset
- ✅ **Aggregation is immutable:** Count all rows once, split by status in the result
- ✅ **Clear separation:** Data layer is independent of presentation layer

If status filtering is needed elsewhere, it should be explicit (e.g., a "Filter by Status" control) and documented as a true filter, not a view mode.
