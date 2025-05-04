// Hotel confirmation specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Date range validation (check-out should be after check-in)
    const fromDateInput = document.querySelector('input[name="from_date"]');
    const toDateInput = document.querySelector('input[name="to_date"]');
    
    if (fromDateInput && toDateInput) {
        const validateDateRange = () => {
            if (fromDateInput.value && toDateInput.value) {
                const fromDate = new Date(fromDateInput.value);
                const toDate = new Date(toDateInput.value);
                
                if (toDate <= fromDate) {
                    toDateInput.classList.add('is-invalid');
                    
                    // Add validation message if doesn't exist
                    let feedback = toDateInput.nextElementSibling;
                    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                        feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback';
                        toDateInput.parentNode.appendChild(feedback);
                    }
                    
                    feedback.textContent = 'Check-out date must be after check-in date';
                } else {
                    toDateInput.classList.remove('is-invalid');
                    const feedback = toDateInput.nextElementSibling;
                    if (feedback && feedback.classList.contains('invalid-feedback')) {
                        feedback.remove();
                    }
                    
                    // Calculate and display number of nights
                    const nights = Math.round((toDate - fromDate) / (1000 * 60 * 60 * 24));
                    const nightsSpan = document.getElementById('nightsCount');
                    if (!nightsSpan) {
                        const span = document.createElement('div');
                        span.id = 'nightsCount';
                        span.className = 'text-muted small mt-1';
                        span.textContent = `${nights} night${nights !== 1 ? 's' : ''}`;
                        toDateInput.parentNode.appendChild(span);
                    } else {
                        nightsSpan.textContent = `${nights} night${nights !== 1 ? 's' : ''}`;
                    }
                }
            }
        };
        
        fromDateInput.addEventListener('change', validateDateRange);
        toDateInput.addEventListener('change', validateDateRange);
        
        // Initialize
        validateDateRange();
    }
    
    // Validate at least one room is selected
    const roomInputs = [
        document.querySelector('input[name="single_rooms"]'),
        document.querySelector('input[name="double_rooms"]'),
        document.querySelector('input[name="twin_rooms"]'),
        document.querySelector('input[name="triple_rooms"]')
    ].filter(Boolean);
    
    const validateRooms = () => {
        const totalRooms = roomInputs.reduce((sum, input) => sum + (parseInt(input.value) || 0), 0);
        const otherRoomsInput = document.querySelector('input[name="other_rooms"]');
        const hasOtherRooms = otherRoomsInput && otherRoomsInput.value.trim() !== '';
        
        if (totalRooms === 0 && !hasOtherRooms) {
            // Add validation message to room configuration section
            const roomDetails = document.getElementById('roomDetails');
            let alertDiv = document.getElementById('roomAlertMessage');
            
            if (!alertDiv) {
                alertDiv = document.createElement('div');
                alertDiv.id = 'roomAlertMessage';
                alertDiv.className = 'alert alert-warning mt-2';
                alertDiv.textContent = 'Please select at least one room type';
                roomDetails.appendChild(alertDiv);
            }
            
            return false;
        } else {
            // Remove validation message if exists
            const alertDiv = document.getElementById('roomAlertMessage');
            if (alertDiv) {
                alertDiv.remove();
            }
            
            return true;
        }
    };
    
    // Add event listeners for room inputs
    roomInputs.forEach(input => {
        if (input) {
            input.addEventListener('change', validateRooms);
        }
    });
    
    const otherRoomsInput = document.querySelector('input[name="other_rooms"]');
    if (otherRoomsInput) {
        otherRoomsInput.addEventListener('input', validateRooms);
    }
    
    // Add validation before form submission
    const form = document.querySelector('form');
    if (form) {
        const originalSubmitHandler = form.onsubmit;
        
        form.onsubmit = function(e) {
            if (!validateRooms()) {
                e.preventDefault();
                alert('Please select at least one room type');
                return false;
            }
            
            if (originalSubmitHandler) {
                return originalSubmitHandler.call(this, e);
            }
        };
    }
});