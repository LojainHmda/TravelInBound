# Request Status as Single Source of Truth

## Core Concept

**Request status is the ONLY status that matters.** It represents the global lifecycle state of the entire request (Requested → Confirmed → Invoiced).

Guides, transport, hotels, restaurants, etc. are **entities that exist inside a request**. They do not have independent statuses.

## The Correct Mental Model

```
Request #101 (Status: CONFIRMED)
├── Guide "Heba" ← Inherits status CONFIRMED from request
├── Hotel "Grand Palace" ← Inherits status CONFIRMED from request
├── Transport (Bus) ← Inherits status CONFIRMED from request
└── Restaurant "Al Reef" ← Inherits status CONFIRMED from request
```

When the request moves from Requested → Confirmed → Invoiced, **all entities move together**. They don't have their own status transitions.

## What Rundown Analytics Represents

**Rundown is NOT tracking the status of a guide itself.**

Instead, it measures: **How many times each entity appears within requests, grouped by request status.**

### Example

Given this data:
- Request #1 (Status: Requested) has guides: Heba, Sami, Ahmed
- Request #2 (Status: Confirmed) has guides: Heba, Kanar
- Request #3 (Status: Invoiced) has guides: Sami

The Rundown should show:
```
Guide Name | Requested | Confirmed | Invoiced
-----------|-----------|-----------|----------
Heba       | 1         | 1         | 0
Sami       | 1         | 0         | 1
Ahmed      | 1         | 0         | 0
Kanar      | 0         | 1         | 0
```

**What this means:**
- "Heba with Requested filter" = How many requests with status Requested have guide Heba assigned
- "Heba with Confirmed filter" = How many requests with status Confirmed have guide Heba assigned

## Implementation Fix

### Before (Wrong)

The aggregation was grouping by **entity status** (which shouldn't exist):

```python
func.sum(_when(InboundGuide.status, 'REQUEST')).label('requested'),
func.sum(_when(InboundGuide.status, 'CONFIRMED')).label('confirmed'),
func.sum(_when(InboundGuide.status, 'INVOICED')).label('invoiced'),
```

This created inconsistency because:
1. Entities had independent statuses that could drift from their request status
2. Aggregation didn't reflect the true request lifecycle

### After (Correct)

Now the aggregation groups by **REQUEST status**:

```python
func.sum(_when(InboundRequest.status, 'REQUEST')).label('requested'),
func.sum(_when(InboundRequest.status, 'CONFIRMED')).label('confirmed'),
func.sum(_when(InboundRequest.status, 'INVOICED')).label('invoiced'),
```

This ensures:
1. All entities inherit request status through their association
2. The counts reflect the true request lifecycle
3. One truth: request status drives everything

## Files Modified

**app/routes/inbound.py** — `supplier_analytics_api()` function

Changed all aggregation queries for all supplier types:
- GUIDE (3 variants: language, service_type, by name)
- TRANSPORT (2 variants: vehicle_type, by supplier)
- RESTAURANT (3 variants: meal_type, location, by restaurant)
- HOTEL (4 variants: category, meal_plan, location, by name)

**Total: 12 changes** — each changed from `InboundGuide.status` / `InboundHotel.status` / etc. to `InboundRequest.status`

## Key Rule for Implementation

**Request status is a property of the request only.**

Entities inside the request inherit visibility through their **association** with the request, not through their own status field.

## Why This Matters

### Before Fix
```
User creates request with guide "Heba"
→ Guide saved with status = 'REQUESTED' (entity-level status)
→ Analytics groups by guide.status
→ Inconsistency: guide status could differ from request status
→ Complex to track when request status changes
```

### After Fix
```
User creates request (status: Requested) with guide "Heba"
→ Guide linked to request
→ Analytics groups by request.status
→ Consistency: guide is always Requested because its request is Requested
→ Simple: when request status changes, guide automatically follows
```

## Testing

**Scenario:** Create a request with guides in April 2026, set request to "Requested"

**Expected behavior:**
```
Guide X appears in:
- Requested tab: ✓ (shown)
- Confirmed tab: ✗ (not shown)
- Invoiced tab: ✗ (not shown)
```

If the request later changes to Confirmed:
```
Guide X appears in:
- Requested tab: ✗ (not shown)
- Confirmed tab: ✓ (shown)
- Invoiced tab: ✗ (not shown)
```

Guide counts remain consistent; only which tab they appear in changes.

## Note on Entity Status Fields

The `status` fields on InboundGuide, InboundHotel, InboundTransport, etc. are now **legacy columns** that should be:
1. Deprecated (no longer updated by the application)
2. Eventually removed in a future refactor
3. Never relied upon for business logic

All aggregation now flows through request status, which is the single source of truth.
