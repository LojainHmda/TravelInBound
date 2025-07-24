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
    // Initialize segment-specific passenger management
    const addSegmentPassengerBtns = document.querySelectorAll('.add-segment-passenger');
    
    addSegmentPassengerBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const segmentIndex = this.getAttribute('data-segment');
            addSegmentPassengerRow(segmentIndex);
        });
    });
    
    // Add event listeners for remove buttons
    updateSegmentRemoveButtons();
}

function addSegmentPassengerRow(segmentIndex) {
    const container = document.getElementById(`segment-passengers-${segmentIndex}`);
    const existingRows = container.querySelectorAll('.passenger-row');
    const newIndex = existingRows.length + 1;
    
    const newRow = document.createElement('div');
    newRow.className = 'passenger-row mb-2';
    newRow.innerHTML = `
        <div class="input-group">
            <span class="input-group-text">Passenger ${newIndex}</span>
            <input type="text" name="segments[${segmentIndex}][passenger_names][]" class="form-control" placeholder="Full name as in passport">
            <input type="text" name="segments[${segmentIndex}][ticket_numbers][]" class="form-control" placeholder="Ticket/E-ticket number">
            <button type="button" class="btn btn-outline-danger remove-segment-passenger">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(newRow);
    updateSegmentRemoveButtons();
}

function updateSegmentRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-segment-passenger');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const row = this.closest('.passenger-row');
            const container = row.closest('[id^="segment-passengers-"]');
            row.remove();
            updateSegmentPassengerNumbers(container);
        });
    });
}

function updateSegmentPassengerNumbers(container) {
    const rows = container.querySelectorAll('.passenger-row');
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

// Function to populate flight form from ticket scanner modal
function populateFlightDetailsFromTicket(flightData) {
    console.log('Populating flight form with extracted data:', flightData);
    
    // Clear existing segments and start fresh
    const segmentsContainer = document.getElementById('flight-segments-container');
    segmentsContainer.innerHTML = '';
    
    // Set flight type
    if (flightData.flight_type) {
        const flightTypeSelect = document.getElementById('flight_type');
        if (flightTypeSelect) {
            flightTypeSelect.value = flightData.flight_type;
        }
    }
    
    // Set booking reference/PNR
    if (flightData.pnr || flightData.booking_reference) {
        const pnrField = document.getElementById('booking_reference');
        if (pnrField) {
            pnrField.value = flightData.pnr || flightData.booking_reference;
        }
    }
    
    // Set travel class
    if (flightData.travel_class) {
        const travelClassSelect = document.querySelector('select[name="travel_class"]');
        if (travelClassSelect) {
            travelClassSelect.value = flightData.travel_class;
        }
    }
    
    // Set terminal
    if (flightData.terminal) {
        const terminalField = document.querySelector('input[name="terminal"]');
        if (terminalField) {
            terminalField.value = flightData.terminal;
        }
    }
    
    // Populate segments with segment-level passenger data
    if (flightData.segments && flightData.segments.length > 0) {
        flightData.segments.forEach((segment, index) => {
            if (index === 0) {
                // First segment - populate existing form fields
                populateSegmentData(0, segment, flightData);
            } else {
                // Additional segments - create new segment forms
                addFlightSegment();
                populateSegmentData(index, segment, flightData);
            }
        });
    } else {
        // Single flight format - populate first segment
        populateSegmentData(0, flightData, flightData);
    }
    
    // Set passenger counts
    if (flightData.passenger_count) {
        const adultsField = document.querySelector('input[name="adults"]');
        const childrenField = document.querySelector('input[name="children"]');
        const infantsField = document.querySelector('input[name="infants"]');
        
        if (adultsField) adultsField.value = flightData.passenger_count.adults || 1;
        if (childrenField) childrenField.value = flightData.passenger_count.children || 0;
        if (infantsField) infantsField.value = flightData.passenger_count.infants || 0;
    }
    
    showSuccessAlert('Flight details populated from ticket scan! Please review and confirm the information.');
}

function populateSegmentData(segmentIndex, segmentData, globalData) {
    // Populate basic flight fields
    const fields = [
        { name: 'airline', value: segmentData.airline },
        { name: 'flight_number', value: segmentData.flight_number },
        { name: 'departure_airport', value: segmentData.departure_airport },
        { name: 'arrival_airport', value: segmentData.arrival_airport },
        { name: 'flight_date', value: segmentData.flight_date },
        { name: 'departure_time', value: segmentData.departure_time },
        { name: 'arrival_time', value: segmentData.arrival_time },
        { name: 'duration', value: segmentData.duration },
        { name: 'aircraft_type', value: segmentData.aircraft_type },
        { name: 'connection_type', value: segmentData.connection_type },
        { name: 'pnr', value: segmentData.pnr || globalData.pnr || globalData.booking_reference }
    ];
    
    fields.forEach(field => {
        if (field.value) {
            const fieldElement = document.getElementById(`${field.name}-${segmentIndex}`) || 
                               document.querySelector(`input[name="segments[${segmentIndex}][${field.name}]"]`);
            if (fieldElement) {
                fieldElement.value = field.value;
            }
        }
    });
    
    // Populate segment-specific passenger data
    const segmentPassengers = segmentData.passenger_names || globalData.passenger_names || [];
    const segmentTickets = segmentData.ticket_numbers || globalData.ticket_numbers || [];
    
    if (segmentPassengers.length > 0) {
        const passengerContainer = document.getElementById(`segment-passengers-${segmentIndex}`);
        if (passengerContainer) {
            // Clear existing passenger rows
            passengerContainer.innerHTML = '';
            
            // Add passenger rows for this segment
            segmentPassengers.forEach((passenger, pIndex) => {
                const ticket = segmentTickets[pIndex] || '';
                
                const passengerRow = document.createElement('div');
                passengerRow.className = 'passenger-row mb-2';
                passengerRow.innerHTML = `
                    <div class="input-group">
                        <span class="input-group-text">Passenger ${pIndex + 1}</span>
                        <input type="text" name="segments[${segmentIndex}][passenger_names][]" class="form-control" 
                               value="${passenger}" placeholder="Full name as in passport">
                        <input type="text" name="segments[${segmentIndex}][ticket_numbers][]" class="form-control" 
                               value="${ticket}" placeholder="Ticket/E-ticket number">
                        <button type="button" class="btn btn-outline-danger remove-segment-passenger">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                passengerContainer.appendChild(passengerRow);
            });
            
            // Update remove button listeners
            updateSegmentRemoveButtons();
        }
    }
}

// Make functions available globally for the scanning modal
window.populateFlightForm = populateFlightForm;
window.populateFlightDetailsFromTicket = populateFlightDetailsFromTicket;