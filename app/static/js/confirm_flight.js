// Flight confirmation specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add passenger function
    const addPassengerBtn = document.getElementById('addPassenger');
    const passengerNames = document.getElementById('passengerNames');
    
    // Calculate the current number of passengers
    let passengerCount = passengerNames ? passengerNames.querySelectorAll('.input-group').length : 1;
    
    // Add event listeners to existing remove passenger buttons
    document.querySelectorAll('.remove-passenger').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.input-group').remove();
        });
    });
    
    if (addPassengerBtn && passengerNames) {
        addPassengerBtn.addEventListener('click', function() {
            passengerCount++;
            let passengerType = 'Adult';
            if (passengerCount > document.querySelector('input[name="adults"]').value) {
                const childrenCount = parseInt(document.querySelector('input[name="children"]').value);
                if (passengerCount <= parseInt(document.querySelector('input[name="adults"]').value) + childrenCount) {
                    passengerType = 'Child';
                } else {
                    passengerType = 'Infant';
                }
            }
            
            const newPassenger = document.createElement('div');
            newPassenger.className = 'input-group mb-2';
            newPassenger.innerHTML = `
                <span class="input-group-text">Passenger ${passengerCount}</span>
                <input type="text" name="passenger_names[]" class="form-control" placeholder="Full name as in passport">
                <button type="button" class="btn btn-outline-danger remove-passenger">
                    <i class="fas fa-times"></i>
                </button>
            `;
            passengerNames.appendChild(newPassenger);
            
            // Add remove event listener
            newPassenger.querySelector('.remove-passenger').addEventListener('click', function() {
                this.closest('.input-group').remove();
            });
        });
        
        // Update passenger fields when counts change
        const updatePassengerFields = () => {
            const adults = parseInt(document.querySelector('input[name="adults"]').value) || 0;
            const children = parseInt(document.querySelector('input[name="children"]').value) || 0;
            const infants = parseInt(document.querySelector('input[name="infants"]').value) || 0;
            const total = adults + children + infants;
            
            // First clear all except the first default field
            const passengerFields = passengerNames.querySelectorAll('.input-group');
            for (let i = 1; i < passengerFields.length; i++) {
                passengerFields[i].remove();
            }
            
            // Then add the required number of fields
            for (let i = 1; i < total; i++) {
                const type = i < adults ? 'Adult' : (i < adults + children ? 'Child' : 'Infant');
                const index = i < adults ? i + 1 : (i < adults + children ? i - adults + 1 : i - adults - children + 1);
                
                const newPassenger = document.createElement('div');
                newPassenger.className = 'input-group mb-2';
                newPassenger.innerHTML = `
                    <span class="input-group-text">${type} ${index}</span>
                    <input type="text" name="passenger_names[]" class="form-control" placeholder="Full name as in passport">
                    <button type="button" class="btn btn-outline-danger remove-passenger">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                passengerNames.appendChild(newPassenger);
                
                // Add remove event listener
                newPassenger.querySelector('.remove-passenger').addEventListener('click', function() {
                    this.closest('.input-group').remove();
                });
            }
        };
        
        const adultsInput = document.querySelector('input[name="adults"]');
        const childrenInput = document.querySelector('input[name="children"]');
        const infantsInput = document.querySelector('input[name="infants"]');
        
        if (adultsInput && childrenInput && infantsInput) {
            adultsInput.addEventListener('change', updatePassengerFields);
            childrenInput.addEventListener('change', updatePassengerFields);
            infantsInput.addEventListener('change', updatePassengerFields);
        }
    }
    
    // Airport autocomplete could be added here
    
    // Validate flight number format
    const flightNumberInput = document.querySelector('input[name="flight_number"]');
    if (flightNumberInput) {
        flightNumberInput.addEventListener('blur', function() {
            const value = this.value.trim();
            const flightNumberPattern = /^[A-Z0-9]{2,3}\s*\d{1,4}[A-Z]?$/i;
            
            if (value && !flightNumberPattern.test(value)) {
                this.classList.add('is-invalid');
                
                // Add validation message if doesn't exist
                let feedback = this.nextElementSibling;
                if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                    feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    this.parentNode.appendChild(feedback);
                }
                
                feedback.textContent = 'Please enter a valid flight number (e.g., BA123, LH456)';
            } else {
                this.classList.remove('is-invalid');
                const feedback = this.nextElementSibling;
                if (feedback && feedback.classList.contains('invalid-feedback')) {
                    feedback.remove();
                }
            }
        });
    }
});