// Flight confirmation form JavaScript
// Handles passenger management with ticket numbers and flight scanning

document.addEventListener('DOMContentLoaded', function() {
    console.log('Flight confirmation form loaded');
    
    // Initialize passenger management
    initializePassengerManagement();
    
    // Initialize flight scanning
    initializeFlightScanning();
});

function initializePassengerManagement() {
    const addPassengerBtn = document.getElementById('addPassenger');
    const passengerContainer = document.getElementById('passengerNames');
    
    if (addPassengerBtn) {
        addPassengerBtn.addEventListener('click', addPassengerRow);
    }
    
    // Add event listeners for remove buttons
    updateRemoveButtons();
}

function addPassengerRow() {
    const container = document.getElementById('passengerNames');
    const existingRows = container.querySelectorAll('.passenger-row');
    const newIndex = existingRows.length + 1;
    
    const newRow = document.createElement('div');
    newRow.className = 'passenger-row mb-2';
    newRow.innerHTML = `
        <div class="input-group">
            <span class="input-group-text">Passenger ${newIndex}</span>
            <input type="text" name="passenger_names[]" class="form-control" placeholder="Full name as in passport">
            <input type="text" name="ticket_numbers[]" class="form-control" placeholder="Ticket/E-ticket number">
            <button type="button" class="btn btn-outline-danger remove-passenger">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(newRow);
    updateRemoveButtons();
}

function updateRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-passenger');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const row = this.closest('.passenger-row');
            row.remove();
            updatePassengerNumbers();
        });
    });
}

function updatePassengerNumbers() {
    const rows = document.querySelectorAll('.passenger-row');
    rows.forEach((row, index) => {
        const label = row.querySelector('.input-group-text');
        if (label) {
            label.textContent = `Passenger ${index + 1}`;
        }
    });
}

function initializeFlightScanning() {
    // Flight scanning modal and AI functionality
    const scanBtn = document.getElementById('scanFlightBtn');
    if (scanBtn) {
        scanBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('ticketScannerModal'));
            modal.show();
        });
    }
}

// Function to populate form from scanned flight data
function populateFlightForm(flightData) {
    console.log('Populating flight form with scanned data:', flightData);
    
    // Clear any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Populate basic flight information if single segment
    if (flightData.segments && flightData.segments.length > 0) {
        const firstSegment = flightData.segments[0];
        
        // Flight details
        const fieldMappings = [
            { field: 'segments[0][airline]', value: firstSegment.airline },
            { field: 'segments[0][flight_number]', value: firstSegment.flight_number },
            { field: 'segments[0][departure_airport]', value: firstSegment.departure_airport },
            { field: 'segments[0][arrival_airport]', value: firstSegment.arrival_airport },
            { field: 'segments[0][flight_date]', value: firstSegment.flight_date },
            { field: 'segments[0][departure_time]', value: firstSegment.departure_time },
            { field: 'segments[0][arrival_time]', value: firstSegment.arrival_time }
        ];
        
        fieldMappings.forEach(mapping => {
            const field = document.querySelector(`[name="${mapping.field}"]`);
            if (field && mapping.value) {
                field.value = mapping.value;
                console.log(`✅ Set ${mapping.field} = ${mapping.value}`);
            }
        });
        
        // Set booking reference/PNR
        if (flightData.booking_reference) {
            const pnrField = document.querySelector('[name="pnr"]');
            if (pnrField) {
                pnrField.value = flightData.booking_reference;
            }
        }
        
        // Set travel class
        if (flightData.travel_class) {
            const classField = document.querySelector('[name="travel_class"]');
            if (classField) {
                classField.value = flightData.travel_class;
            }
        }
    }
    
    // Handle passenger names and ticket numbers
    if (flightData.passenger_names && flightData.passenger_names.length > 0) {
        populatePassengerData(flightData.passenger_names, flightData.ticket_numbers || []);
    }
    
    // Show success notification
    showSuccessAlert('Flight details successfully imported from ticket!');
}

function populatePassengerData(passengerNames, ticketNumbers) {
    const container = document.getElementById('passengerNames');
    if (!container) return;
    
    // Clear existing passenger fields
    container.innerHTML = '';
    
    // Add passenger fields for each name
    passengerNames.forEach((name, index) => {
        const ticketNumber = ticketNumbers[index] || '';
        
        const row = document.createElement('div');
        row.className = 'passenger-row mb-2';
        row.innerHTML = `
            <div class="input-group">
                <span class="input-group-text">Passenger ${index + 1}</span>
                <input type="text" name="passenger_names[]" class="form-control" value="${name}" placeholder="Full name as in passport">
                <input type="text" name="ticket_numbers[]" class="form-control" value="${ticketNumber}" placeholder="Ticket/E-ticket number">
                ${index > 0 ? '<button type="button" class="btn btn-outline-danger remove-passenger"><i class="fas fa-times"></i></button>' : ''}
            </div>
        `;
        
        container.appendChild(row);
    });
    
    // Update passenger count
    const adultsField = document.querySelector('input[name="adults"]');
    if (adultsField) {
        adultsField.value = passengerNames.length;
    }
    
    // Re-initialize remove button handlers
    updateRemoveButtons();
    
    console.log(`✅ Added ${passengerNames.length} passengers with ticket numbers`);
}

function showSuccessAlert(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show mt-3';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert the alert at the top of the form
    const form = document.querySelector('form');
    if (form && form.firstChild) {
        form.insertBefore(alert, form.firstChild);
    }
    
    // Auto-dismiss the alert after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

// Make function available globally for the scanning modal
window.populateFlightForm = populateFlightForm;