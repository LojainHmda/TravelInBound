/**
 * Insurance confirmation form specific JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Insurance confirmation script loaded');
    
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
    
    // Insurance type selections
    const insuranceTypeSelect = document.querySelector('select[name="insurance_type"]');
    
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
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                
                if (endDate < startDate) {
                    endDateInput.setCustomValidity('Coverage end date must be after start date');
                } else {
                    endDateInput.setCustomValidity('');
                }
            }
        };
        
        startDateInput.addEventListener('change', validateDates);
        endDateInput.addEventListener('change', validateDates);
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
        'primary_insured': document.querySelector('input[name="primary_insured"]')?.value,
        'insurance_type': document.querySelector('select[name="insurance_type"]')?.value
    });
});