// payment.js - JavaScript for payment functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('Payment JS loaded');
    
    // Elements for payment handling
    const paymentForm = document.getElementById('payment-form');
    const paymentMethodSelect = document.getElementById('payment_method');
    const paymentNotesTextarea = document.getElementById('payment_notes');
    const paymentStatusBadge = document.getElementById('payment-status-badge');
    const totalPaidAmount = document.getElementById('total-paid-amount');
    const paymentRecordsTable = document.getElementById('payment-records-table');
    const paymentRecordsBody = document.getElementById('payment-records-body');
    
    // Modal elements
    const paymentAmountInput = document.getElementById('payment_amount');
    const paymentModalMethodSelect = document.getElementById('payment_modal_method');
    const transactionIdInput = document.getElementById('transaction_id');
    const paymentDateInput = document.getElementById('payment_date');
    const paymentModalNotesTextarea = document.getElementById('payment_modal_notes');
    const processPaymentBtn = document.getElementById('processPaymentBtn');
    
    // Set default payment date to today
    if (paymentDateInput) {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        paymentDateInput.value = formattedDate;
    }
    
    // Handle process payment button click
    if (processPaymentBtn && paymentAmountInput && paymentModalMethodSelect) {
        processPaymentBtn.addEventListener('click', function() {
            // Get values from modal fields
            const amount = paymentAmountInput.value;
            const method = paymentModalMethodSelect.value;
            const transactionId = transactionIdInput.value;
            const paymentDate = paymentDateInput.value;
            const notes = paymentModalNotesTextarea.value;
            
            // Validate amount
            if (!amount || parseFloat(amount) <= 0) {
                alert('Please enter a valid payment amount');
                return;
            }
            
            // Update the main form fields
            if (paymentMethodSelect) paymentMethodSelect.value = method;
            if (paymentNotesTextarea) paymentNotesTextarea.value = notes;
            
            // Add payment record to the table
            addPaymentRecord({
                date: new Date(paymentDate).toLocaleDateString(),
                method: method,
                amount: parseFloat(amount).toFixed(2),
                notes: notes,
                transaction_id: transactionId
            });
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
            if (modal) modal.hide();
            
            // Submit the payment form with the payment action
            if (paymentForm) {
                const hiddenActionInput = document.createElement('input');
                hiddenActionInput.type = 'hidden';
                hiddenActionInput.name = 'save_action';
                hiddenActionInput.value = 'payment';
                paymentForm.appendChild(hiddenActionInput);
                
                // Add hidden fields for modal values
                const hiddenAmountInput = document.createElement('input');
                hiddenAmountInput.type = 'hidden';
                hiddenAmountInput.name = 'payment_amount';
                hiddenAmountInput.value = amount;
                paymentForm.appendChild(hiddenAmountInput);
                
                const hiddenTransactionInput = document.createElement('input');
                hiddenTransactionInput.type = 'hidden';
                hiddenTransactionInput.name = 'transaction_id';
                hiddenTransactionInput.value = transactionId;
                paymentForm.appendChild(hiddenTransactionInput);
                
                const hiddenDateInput = document.createElement('input');
                hiddenDateInput.type = 'hidden';
                hiddenDateInput.name = 'payment_date';
                hiddenDateInput.value = paymentDate;
                paymentForm.appendChild(hiddenDateInput);
                
                // Submit the form
                paymentForm.submit();
            }
        });
    }
    
    // Function to add a payment record to the table
    function addPaymentRecord(payment) {
        if (!paymentRecordsBody) return;
        
        // Clear the "no payments" row if it exists
        const emptyRow = paymentRecordsBody.querySelector('tr.text-center.text-muted');
        if (emptyRow) {
            paymentRecordsBody.removeChild(emptyRow);
        }
        
        // Create a new row for the payment
        const newRow = document.createElement('tr');
        
        // Add cells for payment details
        newRow.innerHTML = `
            <td>${payment.date}</td>
            <td>${getPaymentMethodText(payment.method)}</td>
            <td>$${payment.amount}</td>
            <td>
                ${payment.notes || ''}
                ${payment.transaction_id ? `<small class="text-muted d-block">Ref: ${payment.transaction_id}</small>` : ''}
            </td>
        `;
        
        // Add the row to the table
        paymentRecordsBody.appendChild(newRow);
        
        // Update the total paid amount (if available)
        if (totalPaidAmount) {
            // Get the current total
            let currentTotal = parseFloat(totalPaidAmount.textContent.replace('$', '')) || 0;
            
            // Add the new payment amount
            currentTotal += parseFloat(payment.amount);
            
            // Update the displayed total
            totalPaidAmount.textContent = `$${currentTotal.toFixed(2)}`;
        }
        
        // Update the payment status badge (if available)
        if (paymentStatusBadge) {
            paymentStatusBadge.textContent = 'Paid';
            paymentStatusBadge.classList.remove('bg-warning', 'text-dark');
            paymentStatusBadge.classList.add('bg-success');
        }
    }
    
    // Helper function to get readable payment method text
    function getPaymentMethodText(method) {
        const methodMap = {
            'CREDIT_CARD': 'Credit Card',
            'BANK_TRANSFER': 'Bank Transfer',
            'PAYPAL': 'PayPal',
            'CASH': 'Cash',
            'OTHER': 'Other'
        };
        
        return methodMap[method] || method;
    }
    
    // Initialize existing payments (if any)
    function initializeExistingPayments() {
        const existingPaymentsData = window.existingPayments || [];
        
        if (existingPaymentsData.length > 0 && paymentRecordsBody) {
            // Clear any existing rows
            paymentRecordsBody.innerHTML = '';
            
            // Add each payment record
            let totalPaid = 0;
            existingPaymentsData.forEach(payment => {
                addPaymentRecord(payment);
                totalPaid += parseFloat(payment.amount);
            });
            
            // Update total paid amount
            if (totalPaidAmount) {
                totalPaidAmount.textContent = `$${totalPaid.toFixed(2)}`;
            }
            
            // Update payment status
            if (paymentStatusBadge) {
                if (totalPaid > 0) {
                    paymentStatusBadge.textContent = 'Paid';
                    paymentStatusBadge.classList.remove('bg-warning', 'text-dark');
                    paymentStatusBadge.classList.add('bg-success');
                }
            }
        }
    }
    
    // Call the initialization function
    initializeExistingPayments();
});