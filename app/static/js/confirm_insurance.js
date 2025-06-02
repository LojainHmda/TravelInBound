/**
 * Insurance confirmation form specific JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Insurance confirmation script loaded');
    
    // Set pre-selected values for dropdowns if they're not already selected
    function setSelectedOption(selectElement, value) {
        if (!selectElement) {
            console.warn('Select element not found');
            return;
        }
        
        if (!value) {
            console.warn('No value to set for', selectElement.name);
            return;
        }
        
        // Try to find and select the option with the matching value
        const options = selectElement.querySelectorAll('option');
        let found = false;
        
        options.forEach(option => {
            if (option.value === value) {
                option.selected = true;
                found = true;
            }
        });
        
        if (!found) {
            console.warn(`Could not find matching option for ${selectElement.name} with value: ${value}`);
        }
    }
    
    // Get saved data from pre-populated fields
    const supplierValue = document.querySelector('input[name="supplier_value"]')?.value;
    const insuranceTypeValue = document.querySelector('input[name="insurance_type_value"]')?.value;
    const currencyValue = document.querySelector('input[name="currency_value"]')?.value;
    
    // Get references to the select elements
    const supplierSelect = document.querySelector('select[name="supplier"]');
    const insuranceTypeSelect = document.querySelector('select[name="insurance_type"]');
    const currencySelect = document.querySelector('select[name="currency"]');
    
    // Set values in select elements only if they need to be set by JS
    // The template should have already set selected attributes
    if (supplierSelect && supplierValue && !supplierSelect.value) {
        setSelectedOption(supplierSelect, supplierValue);
    }
    
    if (insuranceTypeSelect && insuranceTypeValue && !insuranceTypeSelect.value) {
        setSelectedOption(insuranceTypeSelect, insuranceTypeValue);
    }
    
    if (currencySelect && currencyValue && !currencySelect.value) {
        setSelectedOption(currencySelect, currencyValue);
    }
    
    // Add insured person functionality
    const addInsuredBtn = document.getElementById('addInsured');
    const additionalInsured = document.getElementById('additionalInsured');
    
    if (addInsuredBtn && additionalInsured) {
        // Add event listener to add button
        addInsuredBtn.addEventListener('click', function() {
            const newRow = document.createElement('div');
            newRow.className = 'input-group mb-2';
            newRow.innerHTML = `
                <input type="text" name="additional_insured[]" class="form-control" placeholder="Full name">
                <button type="button" class="btn btn-outline-danger remove-person">
                    <i class="fas fa-times"></i>
                </button>
            `;
            additionalInsured.appendChild(newRow);
            
            // Add remove event listener to the new row
            newRow.querySelector('.remove-person').addEventListener('click', function() {
                this.closest('.input-group').remove();
            });
        });
        
        // Add remove event listener to the initial row
        const removeButtons = additionalInsured.querySelectorAll('.remove-person');
        removeButtons.forEach(button => {
            button.addEventListener('click', function() {
                this.closest('.input-group').remove();
            });
        });
    }
    
    // Insurance type selections - we already have the reference from earlier
    if (insuranceTypeSelect) {
        insuranceTypeSelect.addEventListener('change', function() {
            const insuranceType = this.value;
            
            // Auto-check relevant coverage options based on insurance type
            if (insuranceType === 'Travel Medical') {
                document.getElementById('coverage_medical').checked = true;
                document.getElementById('coverage_evacuation').checked = true;
            } else if (insuranceType === 'Trip Cancellation') {
                document.getElementById('coverage_cancellation').checked = true;
                document.getElementById('coverage_delay').checked = true;
            } else if (insuranceType === 'Comprehensive') {
                document.getElementById('coverage_medical').checked = true;
                document.getElementById('coverage_evacuation').checked = true;
                document.getElementById('coverage_cancellation').checked = true;
                document.getElementById('coverage_baggage').checked = true;
                document.getElementById('coverage_delay').checked = true;
                document.getElementById('coverage_personal').checked = true;
            } else if (insuranceType === 'Baggage') {
                document.getElementById('coverage_baggage').checked = true;
            } else if (insuranceType === 'Adventure') {
                document.getElementById('coverage_medical').checked = true;
                document.getElementById('coverage_evacuation').checked = true;
                document.getElementById('coverage_activities').checked = true;
            }
        });
    }
    
    // Date validation
    const startDateInput = document.querySelector('input[name="coverage_start"]');
    const endDateInput = document.querySelector('input[name="coverage_end"]');
    
    if (startDateInput && endDateInput) {
        const validateDates = () => {
            if (startDateInput.value && endDateInput.value) {
                try {
                    const startDate = new Date(startDateInput.value);
                    const endDate = new Date(endDateInput.value);
                    
                    if (endDate < startDate) {
                        endDateInput.setCustomValidity('Coverage end date must be after start date');
                    } else {
                        endDateInput.setCustomValidity('');
                    }
                } catch (e) {
                    console.error('Error validating dates:', e);
                }
            }
        };
        
        try {
            startDateInput.addEventListener('change', validateDates);
            endDateInput.addEventListener('change', validateDates);
            // Run validation initially
            validateDates();
        } catch (e) {
            console.error('Error setting up date validation:', e);
        }
    }

    // Helper function to add options to select elements
    function addOption(selectElement, value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        selectElement.appendChild(option);
    }

    // Initialize any other insurance-specific behavior here
});