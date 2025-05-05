/**
 * Insurance confirmation form specific JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Insurance confirmation script loaded');
    
    // Policy type dependent fields
    const policyTypeSelect = document.querySelector('select[name="policy_type"]');
    const coverageTypeSelect = document.querySelector('select[name="coverage_type"]');
    
    if (policyTypeSelect) {
        policyTypeSelect.addEventListener('change', function() {
            const policyType = this.value;
            
            // Update coverage type options based on policy type
            if (coverageTypeSelect) {
                // Clear existing options
                coverageTypeSelect.innerHTML = '';
                
                // Add options based on policy type
                if (policyType === 'Travel') {
                    addOption(coverageTypeSelect, 'Comprehensive', 'Comprehensive');
                    addOption(coverageTypeSelect, 'Medical Only', 'Medical Only');
                    addOption(coverageTypeSelect, 'Cancellation Only', 'Cancellation Only');
                    addOption(coverageTypeSelect, 'Baggage Only', 'Baggage Only');
                } else if (policyType === 'Medical') {
                    addOption(coverageTypeSelect, 'Basic', 'Basic');
                    addOption(coverageTypeSelect, 'Standard', 'Standard');
                    addOption(coverageTypeSelect, 'Premium', 'Premium');
                } else if (policyType === 'Life') {
                    addOption(coverageTypeSelect, 'Term', 'Term');
                    addOption(coverageTypeSelect, 'Whole Life', 'Whole Life');
                    addOption(coverageTypeSelect, 'Universal', 'Universal');
                } else {
                    // Default options
                    addOption(coverageTypeSelect, 'Basic', 'Basic');
                    addOption(coverageTypeSelect, 'Standard', 'Standard');
                    addOption(coverageTypeSelect, 'Premium', 'Premium');
                }
            }
        });
    }
    
    // Date validation for insurance policy validity
    const startDateField = document.querySelector('input[name="start_date"]');
    const endDateField = document.querySelector('input[name="end_date"]');
    
    if (startDateField && endDateField) {
        const validateDates = () => {
            if (startDateField.value && endDateField.value) {
                const startDate = new Date(startDateField.value);
                const endDate = new Date(endDateField.value);
                
                if (endDate <= startDate) {
                    endDateField.setCustomValidity('End date must be after start date');
                } else {
                    endDateField.setCustomValidity('');
                }
            }
        };
        
        startDateField.addEventListener('change', validateDates);
        endDateField.addEventListener('change', validateDates);
    }
    
    // Premium amount calculation based on coverage amount
    const coverageAmountField = document.querySelector('input[name="coverage_amount"]');
    const premiumAmountField = document.querySelector('input[name="premium_amount"]');
    
    if (coverageAmountField && premiumAmountField) {
        coverageAmountField.addEventListener('change', function() {
            // Simple calculation for example purposes
            const coverageAmount = parseFloat(this.value) || 0;
            const premiumAmount = (coverageAmount * 0.05).toFixed(2); // 5% of coverage amount
            premiumAmountField.value = premiumAmount;
        });
    }
    
    // Helper function to add options to select elements
    function addOption(selectElement, value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        selectElement.appendChild(option);
    }

    // Debug information
    console.log('Insurance form data loaded:', {
        'policy_number': document.querySelector('input[name="policy_number"]')?.value,
        'insurance_company': document.querySelector('input[name="insurance_company"]')?.value,
        'policy_type': document.querySelector('select[name="policy_type"]')?.value
    });
});