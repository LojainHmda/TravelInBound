// Hotel confirmation specific functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Hotel confirmation script loaded');
    
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
        
        console.log(`Setting ${selectElement.name} to value: '${value}'`);
        
        // Try to find and select the option with the matching value
        const options = selectElement.querySelectorAll('option');
        let found = false;
        
        options.forEach(option => {
            if (option.value === value) {
                option.selected = true;
                found = true;
                console.log(`Found exact match for ${selectElement.name}: ${value}`);
            }
        });
        
        if (!found) {
            console.warn(`Could not find matching option for ${selectElement.name} with value: ${value}`);
        }
    }
    
    // Get saved data from pre-populated fields
    const supplierValue = document.querySelector('input[name="supplier_value"]')?.value;
    const mealPlanValue = document.querySelector('input[name="meal_plan_value"]')?.value;
    const statusValue = document.querySelector('input[name="status_value"]')?.value;
    const currencyValue = document.querySelector('input[name="currency_value"]')?.value;
    
    // Get references to the select elements
    const supplierSelect = document.querySelector('select[name="supplier"]');
    const mealPlanSelect = document.querySelector('select[name="meal_plan"]');
    const statusSelect = document.querySelector('select[name="status"]');
    const currencySelect = document.querySelector('select[name="currency"]');
    
    // Set values in select elements only if they need to be set by JS
    // The template should have already set selected attributes
    if (supplierSelect && supplierValue && !supplierSelect.value) {
        setSelectedOption(supplierSelect, supplierValue);
    }
    
    if (mealPlanSelect && mealPlanValue && !mealPlanSelect.value) {
        setSelectedOption(mealPlanSelect, mealPlanValue);
    }
    
    if (statusSelect && statusValue && !statusSelect.value) {
        setSelectedOption(statusSelect, statusValue);
    }
    
    if (currencySelect && currencyValue && !currencySelect.value) {
        setSelectedOption(currencySelect, currencyValue);
    }
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
    
    // Dynamic room management system
    let roomCounter = 1;
    
    // Load existing rooms from confirmation data if available
    window.loadExistingHotelRooms = function() {
        try {
            const confirmationDataInput = document.querySelector('input[name="confirmation_data"]');
            if (confirmationDataInput && confirmationDataInput.value) {
                const data = JSON.parse(confirmationDataInput.value);
                if (data.rooms && Array.isArray(data.rooms)) {
                    // Clear existing rooms first
                    const container = document.getElementById('hotelRoomsContainer');
                    container.innerHTML = '';
                    roomCounter = 0;
                    
                    // Add each room from the data
                    data.rooms.forEach(roomData => {
                        addHotelRoom(roomData);
                    });
                }
            }
        } catch (e) {
            console.log('No existing room data to load:', e);
        }
    };
    
    // Initialize existing rooms if available
    setTimeout(loadExistingHotelRooms, 100);
});

// Global functions for room management
function addHotelRoom(roomData = null) {
    const container = document.getElementById('hotelRoomsContainer');
    const roomIndex = container.children.length;
    
    const roomCard = document.createElement('div');
    roomCard.className = 'hotel-room-card mb-3';
    roomCard.style.cssText = 'border: 2px solid #007bff; border-radius: 8px; padding: 15px; background-color: #f8f9fa;';
    
    roomCard.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0 text-primary">🏨 Room ${roomIndex + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeHotelRoom(this)" ${roomIndex === 0 ? 'style="display: none;"' : ''}>
                <i class="fas fa-trash"></i>
            </button>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <label class="form-label">Room Type</label>
                <select name="rooms[${roomIndex}][room_type]" class="form-control">
                    <option value="">Select Room Type</option>
                    <option value="Single Room">Single Room</option>
                    <option value="Double Room">Double Room</option>
                    <option value="Twin Room">Twin Room</option>
                    <option value="Triple Room">Triple Room</option>
                    <option value="Family Room">Family Room</option>
                    <option value="Suite">Suite</option>
                    <option value="Junior Suite">Junior Suite</option>
                    <option value="Executive Suite">Executive Suite</option>
                    <option value="Presidential Suite">Presidential Suite</option>
                    <option value="Connecting Rooms">Connecting Rooms</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label">Board Basis</label>
                <select name="rooms[${roomIndex}][board_basis]" class="form-control">
                    <option value="Room Only">Room Only</option>
                    <option value="Bed & Breakfast (BB)">Bed & Breakfast (BB)</option>
                    <option value="Half Board (HB)">Half Board (HB)</option>
                    <option value="Full Board (FB)">Full Board (FB)</option>
                    <option value="All Inclusive (AI)">All Inclusive (AI)</option>
                    <option value="Ultra All Inclusive">Ultra All Inclusive</option>
                </select>
            </div>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-4">
                <label class="form-label">Adults</label>
                <input type="number" name="rooms[${roomIndex}][adults]" class="form-control" value="2" min="1" max="6">
            </div>
            <div class="col-md-4">
                <label class="form-label">Children</label>
                <input type="number" name="rooms[${roomIndex}][children]" class="form-control" value="0" min="0" max="4">
            </div>
            <div class="col-md-4">
                <label class="form-label">Lead Passenger Name</label>
                <input type="text" name="rooms[${roomIndex}][lead_passenger]" class="form-control" placeholder="Mr. YOUSEF">
            </div>
        </div>
    `;
    
    container.appendChild(roomCard);
    
    // Populate with existing data if provided
    if (roomData) {
        const roomTypeSelect = roomCard.querySelector(`select[name="rooms[${roomIndex}][room_type]"]`);
        const boardBasisSelect = roomCard.querySelector(`select[name="rooms[${roomIndex}][board_basis]"]`);
        const adultsInput = roomCard.querySelector(`input[name="rooms[${roomIndex}][adults]"]`);
        const childrenInput = roomCard.querySelector(`input[name="rooms[${roomIndex}][children]"]`);
        const leadPassengerInput = roomCard.querySelector(`input[name="rooms[${roomIndex}][lead_passenger]"]`);
        
        if (roomData.room_type) roomTypeSelect.value = roomData.room_type;
        if (roomData.board_basis) boardBasisSelect.value = roomData.board_basis;
        if (roomData.adults) adultsInput.value = roomData.adults;
        if (roomData.children) childrenInput.value = roomData.children;
        if (roomData.lead_passenger) leadPassengerInput.value = roomData.lead_passenger;
    }
    
    // Update room numbers and delete button visibility
    updateRoomNumbers();
}

function removeHotelRoom(button) {
    const roomCard = button.closest('.hotel-room-card');
    roomCard.remove();
    updateRoomNumbers();
}

function updateRoomNumbers() {
    const container = document.getElementById('hotelRoomsContainer');
    const roomCards = container.querySelectorAll('.hotel-room-card');
    
    roomCards.forEach((card, index) => {
        // Update room title
        const title = card.querySelector('h6');
        title.textContent = `🏨 Room ${index + 1}`;
        
        // Update input names
        const inputs = card.querySelectorAll('input, select');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            if (name && name.includes('rooms[')) {
                const newName = name.replace(/rooms\[\d+\]/, `rooms[${index}]`);
                input.setAttribute('name', newName);
            }
        });
        
        // Show/hide delete button (first room can't be deleted)
        const deleteButton = card.querySelector('.btn-outline-danger');
        if (index === 0) {
            deleteButton.style.display = 'none';
        } else {
            deleteButton.style.display = 'inline-block';
        }
    });
}

// Function to populate hotel form from AI scanning
function populateHotelFormFromScan(data) {
    console.log('Populating hotel form from AI scan:', data);
    
    // Basic hotel information
    if (data.hotel_name) {
        const hotelNameInput = document.querySelector('input[name="hotel_name"]');
        if (hotelNameInput) hotelNameInput.value = data.hotel_name;
    }
    
    if (data.checkin_date) {
        const checkinInput = document.querySelector('input[name="from_date"]');
        if (checkinInput) checkinInput.value = data.checkin_date;
    }
    
    if (data.checkout_date) {
        const checkoutInput = document.querySelector('input[name="to_date"]');
        if (checkoutInput) checkoutInput.value = data.checkout_date;
    }
    
    if (data.confirmation_number) {
        const confirmationInput = document.querySelector('input[name="confirmation_number"]');
        if (confirmationInput) confirmationInput.value = data.confirmation_number;
    }
    
    // If room data is provided, populate the room structure
    if (data.rooms && Array.isArray(data.rooms) && data.rooms.length > 0) {
        // Clear existing rooms and add scanned rooms
        const container = document.getElementById('hotelRoomsContainer');
        container.innerHTML = '';
        
        data.rooms.forEach(roomData => {
            addHotelRoom(roomData);
        });
    } else if (data.room_type || data.guests) {
        // Legacy single room data - convert to new format
        const container = document.getElementById('hotelRoomsContainer');
        container.innerHTML = '';
        
        const roomData = {
            room_type: data.room_type || '',
            board_basis: data.meal_plan || 'Room Only',
            adults: parseInt(data.guests) || 2,
            children: 0,
            lead_passenger: ''
        };
        
        addHotelRoom(roomData);
    }
}