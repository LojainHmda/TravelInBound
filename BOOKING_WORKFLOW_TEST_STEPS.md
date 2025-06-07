# Complete Booking Workflow Test Steps

## Overview
Complete end-to-end testing of booking creation, service confirmation, invoicing, voucher generation, and finance dashboard integration.

## Prerequisites
- Travel booking system running on port 5000
- Test customer and user data available
- Finance module enabled

---

## Step 1: Create New Booking

### 1.1 Navigate to New Booking
1. Go to `/booking/new`
2. Click "Create New Booking" button

### 1.2 Fill Booking Details
1. **Customer Selection**: Select existing customer or add new one
2. **Service Type**: Choose "Flight", "Hotel", "Transport", etc.
3. **Dates**: Set start and end dates
4. **Description**: Add detailed service description
5. **Amount**: Enter service cost (optional)
6. Click "Create Booking Request"

### 1.3 Verify Booking Creation
- Note the booking reference number (e.g., IR-XXXXX)
- Confirm booking status shows "REQUEST"
- Service items appear with status "REQUEST"

---

## Step 2: Progress Booking to Operations

### 2.1 Update Booking Status
1. In booking details page, find "Update Status" section
2. Change status from "REQUEST" to "IN_PROGRESS"
3. Add notes if needed
4. Click "Update Status"

### 2.2 Verify Status Change
- Booking status now shows "IN_PROGRESS"
- Service confirmation buttons become enabled
- Yellow "Save Request" and green "Confirm" buttons appear

---

## Step 3: Confirm Services (Test Popup System)

### 3.1 Test Save Request Function
1. For each unconfirmed service item:
   - Click yellow "Save Request" button
   - Verify it saves without requiring all fields
   - Service remains in "REQUEST" status

### 3.2 Test Popup Confirmation
1. Click green "Confirm" button on a service item
2. **Expected**: Popup modal appears with:
   - Service details summary
   - Verification checklist
   - Warning about completion
   - "Yes, Confirm Service" button

### 3.3 Complete Service Confirmation
1. In the popup modal, click "Yes, Confirm Service"
2. Fill in confirmation details:
   - **Confirmation Reference**: Enter supplier confirmation code
   - **Supplier**: Select or enter supplier name
   - **Cost Amount**: Enter actual cost (if different)
   - **Additional Details**: Service-specific fields
3. Click final "Confirm" button

### 3.4 Verify Service Confirmation
- Service status changes to "CONFIRMED"
- Green confirmation badge appears
- Supplier payment record created automatically
- Service ready for invoicing

---

## Step 4: Generate Invoice

### 4.1 Invoice All Services
1. In booking details, click "Generate Invoice" button
2. Select services to include (or select all)
3. Review invoice details
4. Click "Generate Invoice"

### 4.2 Verify Invoice Generation
- Invoice number assigned (e.g., INV-XXXXX)
- Invoice date recorded
- Booking status may change to "COMPLETED"
- Service items marked as "invoiced"

---

## Step 5: Issue Voucher

### 5.1 Generate Voucher
1. In booking details, look for "Generate Voucher" option
2. Click "Generate Voucher" or "Issue Voucher"
3. Review voucher details:
   - Customer information
   - Service details
   - Confirmation numbers
   - Supplier information

### 5.2 Verify Voucher Content
Check voucher includes:
- Customer name and contact details
- Service descriptions and dates
- Confirmation references
- Supplier contact information
- Terms and conditions
- Emergency contact information

---

## Step 6: Print Voucher

### 6.1 Print/Download Voucher
1. Click "Print Voucher" or "Download PDF"
2. **Expected**: PDF document opens with properly formatted voucher
3. Verify PDF contains all necessary information
4. Test actual printing if needed

---

## Step 7: Verify Finance Dashboard

### 7.1 Navigate to Finance Dashboard
1. Go to `/finance` or click "Finance" in main navigation
2. Access finance dashboard

### 7.2 Check Invoice Records
1. Verify new invoice appears in invoice list
2. Check invoice status and amount
3. Confirm customer and booking reference links

### 7.3 Check Supplier Payments
1. Navigate to supplier payments section
2. Verify automatic supplier payment records created
3. Check amounts match confirmed service costs
4. Verify supplier information is correct

### 7.4 Check Financial Totals
1. Verify dashboard totals updated:
   - Total invoices amount
   - Outstanding supplier payments
   - Revenue calculations
2. Check profit/loss calculations if available

---

## Step 8: Verify Booking Status Updates

### 8.1 Check Final Booking Status
1. Return to booking details page
2. Verify booking status progression:
   - Started as "REQUEST"
   - Changed to "IN_PROGRESS"
   - Final status "COMPLETED" (if all services confirmed and invoiced)

### 8.2 Check Service Item Status
1. All service items show "CONFIRMED" status
2. Invoice numbers assigned to services
3. No outstanding confirmation actions

---

## Expected Results Summary

✓ **Booking Created**: Reference number assigned, status "REQUEST"
✓ **Status Progression**: REQUEST → IN_PROGRESS → COMPLETED
✓ **Service Confirmation**: Popup system works, services confirmed
✓ **Invoice Generated**: Invoice number assigned, amount calculated
✓ **Voucher Issued**: PDF voucher created with all details
✓ **Finance Updated**: Dashboard shows new invoice and supplier payments
✓ **Workflow Complete**: All statuses updated correctly

---

## Troubleshooting Common Issues

### Popup Not Appearing
- Check browser console for JavaScript errors
- Verify Bootstrap is loaded
- Try browser refresh

### Invoice Generation Fails
- Ensure all services are confirmed
- Check service amounts are set
- Verify customer information is complete

### Finance Dashboard Not Updated
- Check if finance module is enabled
- Verify database connections
- Look for any error messages

### Voucher Generation Issues
- Confirm booking has invoice
- Check customer contact details
- Verify service confirmation details

---

## Test Data Cleanup

After testing, you may want to:
1. Delete test bookings if needed
2. Remove test invoice records
3. Clear test supplier payments
4. Reset any test customer data

**Note**: Only delete test data, never production data.