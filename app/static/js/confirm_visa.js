/**
 * Visa confirmation form specific JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Visa confirmation script loaded');
    
    // Visa application status dependent fields
    const statusSelect = document.querySelector('select[name="application_status"]');
    const validFromField = document.querySelector('input[name="valid_from"]');
    const validUntilField = document.querySelector('input[name="valid_until"]');
    const entriesField = document.querySelector('select[name="number_of_entries"]');
    
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            const status = this.value;
            
            // Show/hide visa validity fields based on status
            const validityFields = document.querySelectorAll('input[name="valid_from"], input[name="valid_until"], select[name="number_of_entries"]');
            validityFields.forEach(field => {
                // Check if field exists and has a parent element with mb-3 class
                const fieldContainer = field ? field.closest('.mb-3') : null;
                
                if (status === 'Approved') {
                    if (field) field.required = true;
                    if (fieldContainer) fieldContainer.style.display = 'block';
                } else {
                    if (field) field.required = false;
                    if (fieldContainer) {
                        if (status === 'Rejected') {
                            fieldContainer.style.display = 'none';
                        } else {
                            fieldContainer.style.display = 'block';
                        }
                    }
                }
            });
        });
        
        try {
            // Initialize based on default value
            statusSelect.dispatchEvent(new Event('change'));
        } catch (e) {
            console.error('Error dispatching change event:', e);
        }
    }
    
    // Date validation for visa validity
    if (validFromField && validUntilField) {
        const validateDates = () => {
            if (validFromField.value && validUntilField.value) {
                try {
                    const fromDate = new Date(validFromField.value);
                    const untilDate = new Date(validUntilField.value);
                    
                    if (untilDate <= fromDate) {
                        validUntilField.setCustomValidity('Valid until date must be after valid from date');
                    } else {
                        validUntilField.setCustomValidity('');
                    }
                } catch (e) {
                    console.error('Error validating visa dates:', e);
                }
            }
        };
        
        try {
            validFromField.addEventListener('change', validateDates);
            validUntilField.addEventListener('change', validateDates);
            // Run validation initially
            validateDates();
        } catch (e) {
            console.error('Error setting up visa date validation:', e);
        }
    }

    // Debug information
    console.log('Visa form data loaded:', {
        'applicant_name': document.querySelector('input[name="applicant_name"]')?.value,
        'passport_number': document.querySelector('input[name="passport_number"]')?.value,
        'destination_country': document.querySelector('input[name="destination_country"]')?.value
    });
});