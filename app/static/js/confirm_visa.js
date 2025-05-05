/**
 * Visa confirmation form specific JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Visa confirmation script loaded');
    
    // Set pre-selected values for dropdowns
    function setSelectedOption(selectElement, value) {
        if (!selectElement || !value) return;
        
        // Try to find and select the option with the matching value
        const options = selectElement.querySelectorAll('option');
        let found = false;
        
        options.forEach(option => {
            if (option.value === value) {
                option.selected = true;
                found = true;
            }
        });
        
        // If exact match wasn't found, try a case-insensitive match
        if (!found) {
            options.forEach(option => {
                if (option.value.toLowerCase() === value.toLowerCase()) {
                    option.selected = true;
                }
            });
        }
    }
    
    // Get saved data from pre-populated fields
    const supplierValue = document.querySelector('input[name="supplier_value"]')?.value;
    const visaTypeValue = document.querySelector('input[name="visa_type_value"]')?.value;
    const applicationStatusValue = document.querySelector('input[name="application_status_value"]')?.value;
    const entriesValue = document.querySelector('input[name="number_of_entries_value"]')?.value;
    const processingTypeValue = document.querySelector('input[name="processing_type_value"]')?.value;
    
    // Set values in select elements
    setSelectedOption(document.querySelector('select[name="supplier"]'), supplierValue);
    setSelectedOption(document.querySelector('select[name="visa_type"]'), visaTypeValue);
    setSelectedOption(document.querySelector('select[name="application_status"]'), applicationStatusValue);
    setSelectedOption(document.querySelector('select[name="number_of_entries"]'), entriesValue);
    setSelectedOption(document.querySelector('select[name="processing_type"]'), processingTypeValue);
    
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
    const hiddenFields = {
        'supplier_value': document.querySelector('input[name="supplier_value"]')?.value,
        'visa_type_value': document.querySelector('input[name="visa_type_value"]')?.value,
        'application_status_value': document.querySelector('input[name="application_status_value"]')?.value,
        'number_of_entries_value': document.querySelector('input[name="number_of_entries_value"]')?.value,
        'processing_type_value': document.querySelector('input[name="processing_type_value"]')?.value
    };
    
    console.log('Visa form data loaded:', {
        'applicant_name': document.querySelector('input[name="applicant_name"]')?.value,
        'passport_number': document.querySelector('input[name="passport_number"]')?.value,
        'destination_country': document.querySelector('input[name="destination_country"]')?.value,
        'Hidden values': hiddenFields,
        'Current supplier dropdown value': document.querySelector('select[name="supplier"]')?.value
    });
});