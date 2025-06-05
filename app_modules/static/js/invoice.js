document.addEventListener('DOMContentLoaded', function() {
    // Check if we have invoice generation elements
    const createInvoiceBtn = document.getElementById('createInvoiceBtn');
    
    if (createInvoiceBtn) {
        // Set up event listener for invoice generation
        createInvoiceBtn.addEventListener('click', function() {
            // Get form data
            const invoiceTotal = document.getElementById('invoice_total').value;
            const invoiceNotes = document.getElementById('invoice_modal_notes').value;
            
            // Create a hidden form for generating an invoice
            const form = document.createElement('form');
            form.method = 'POST';
            
            // First, try to get reference_number from the form to check if we're in new booking mode
            const referenceInput = document.querySelector('input[name="request_id"]');
            let isNewBooking = false;
            let reference = '';
            
            if (referenceInput) {
                isNewBooking = true;
                reference = referenceInput.value;
            } else {
                // We're in an existing booking view
                const bookingIdMatch = window.location.pathname.match(/\/booking\/(\d+)/);
                if (bookingIdMatch && bookingIdMatch[1]) {
                    const bookingId = bookingIdMatch[1];
                    form.action = `/booking/${bookingId}/generate_invoice`;
                }
            }
            
            // If we're in new booking mode, save the form first with special flags
            if (isNewBooking) {
                // Get the main form
                const mainForm = document.getElementById('newBookingForm');
                
                // Create hidden input for invoice notes
                const notesInput = document.createElement('input');
                notesInput.type = 'hidden';
                notesInput.name = 'invoice_notes';
                notesInput.value = invoiceNotes;
                mainForm.appendChild(notesInput);
                
                // Create hidden input for total
                if (invoiceTotal) {
                    const totalInput = document.createElement('input');
                    totalInput.type = 'hidden';
                    totalInput.name = 'invoice_total';
                    totalInput.value = invoiceTotal;
                    mainForm.appendChild(totalInput);
                }
                
                // Create hidden input to indicate this is a generate invoice action
                const actionInput = document.createElement('input');
                actionInput.type = 'hidden';
                actionInput.name = 'save_action';
                actionInput.value = 'generate_invoice';
                mainForm.appendChild(actionInput);
                
                // Submit the main form
                mainForm.submit();
                return;
            }
            
            // Create CSRF token input
            const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfTokenMeta) {
                const csrfToken = csrfTokenMeta.getAttribute('content');
                const tokenInput = document.createElement('input');
                tokenInput.type = 'hidden';
                tokenInput.name = 'csrf_token';
                tokenInput.value = csrfToken;
                form.appendChild(tokenInput);
            }
            
            // Create notes input
            const notesInput = document.createElement('input');
            notesInput.type = 'hidden';
            notesInput.name = 'notes';
            notesInput.value = invoiceNotes;
            form.appendChild(notesInput);
            
            // Create total input
            if (invoiceTotal) {
                const totalInput = document.createElement('input');
                totalInput.type = 'hidden';
                totalInput.name = 'total_amount';
                totalInput.value = invoiceTotal;
                form.appendChild(totalInput);
            }
            
            // Append the form to the body and submit it
            document.body.appendChild(form);
            form.submit();
        });
    }
    
    // Initialize invoice modal with calculated total
    const invoiceModal = document.getElementById('invoiceModal');
    if (invoiceModal) {
        invoiceModal.addEventListener('show.bs.modal', function() {
            // Calculate total from line items (for new booking form)
            let total = 0;
            const serviceItemRows = document.querySelectorAll('.service-item-row');
            
            if (serviceItemRows.length > 0) {
                serviceItemRows.forEach(row => {
                    const amountCell = row.querySelector('.item-amount');
                    if (amountCell) {
                        const amount = parseFloat(amountCell.textContent.replace(/[^0-9.-]+/g, ''));
                        if (!isNaN(amount)) {
                            total += amount;
                        }
                    }
                });
            }
            
            // Set the calculated total
            const invoiceTotalInput = document.getElementById('invoice_total');
            if (invoiceTotalInput) {
                invoiceTotalInput.value = total.toFixed(2);
            }
        });
    }
});