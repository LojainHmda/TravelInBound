// Hotel confirmation form functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Hotel confirmation form loaded');
    
    // Initialize hotel room management
    initializeHotelRoomManagement();
    
    // Initialize hotel scanning
    initializeHotelScanning();
});

function initializeHotelRoomManagement() {
    // Initialize room management functionality
    updateRoomRemoveButtons();
}

function createRoomHtml(roomIndex) {
    return `
        <div class="hotel-room-card mb-3" style="border: 2px solid #007bff; border-radius: 8px; padding: 15px; background-color: #f8f9fa;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 text-primary">🏨 Room ${roomIndex + 1}</h6>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeHotelRoom(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-3">
                    <label class="form-label">Room Count</label>
                    <input type="number" name="rooms[${roomIndex}][room_count]" class="form-control" value="1" min="1" max="10">
                    <small class="text-muted">Rooms of this type</small>
                </div>
                <div class="col-md-4">
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
                <div class="col-md-5">
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
        </div>
    `;
}

function addHotelRoom() {
    const container = document.getElementById('hotelRoomsContainer');
    const roomCount = container.children.length;
    const newRoomIndex = roomCount;
    
    const newRoomHtml = createRoomHtml(newRoomIndex);
    
    container.insertAdjacentHTML('beforeend', newRoomHtml);
    updateRoomRemoveButtons();
}

function removeHotelRoom(button) {
    const roomCard = button.closest('.hotel-room-card');
    const container = document.getElementById('hotelRoomsContainer');
    
    // Don't allow removing the last room
    if (container.children.length > 1) {
        roomCard.remove();
        updateRoomNumbers();
        updateRoomRemoveButtons();
    }
}

function updateRoomNumbers() {
    const container = document.getElementById('hotelRoomsContainer');
    const rooms = container.querySelectorAll('.hotel-room-card');
    
    rooms.forEach((room, index) => {
        // Update room title
        const title = room.querySelector('h6');
        title.textContent = `🏨 Room ${index + 1}`;
        
        // Update field names
        const inputs = room.querySelectorAll('input, select');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            if (name && name.includes('rooms[')) {
                const newName = name.replace(/rooms\[\d+\]/, `rooms[${index}]`);
                input.setAttribute('name', newName);
            }
        });
    });
}

function updateRoomRemoveButtons() {
    const container = document.getElementById('hotelRoomsContainer');
    const removeButtons = container.querySelectorAll('.btn-outline-danger');
    
    // Hide remove button if only one room, show for multiple rooms
    removeButtons.forEach((btn, index) => {
        if (container.children.length === 1) {
            btn.style.display = 'none';
        } else {
            btn.style.display = 'inline-block';
        }
    });
}

// Room count management functions removed - each room now has its own count field

function initializeHotelScanning() {
    // Hotel scanning modal and AI functionality
    const modal = document.getElementById('hotelScannerModal');
    const uploadForm = document.getElementById('modalHotelUploadForm');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            analyzeHotelVoucher();
        });
    }
    
    // Ensure Fill Form button is properly connected
    setTimeout(() => {
        const fillButton = document.getElementById('fillHotelForm');
        if (fillButton && !fillButton.hasListener) {
            fillButton.addEventListener('click', function(e) {
                e.preventDefault();
                fillHotelForm();
            });
            fillButton.hasListener = true;
        }
    }, 500);
}

function analyzeHotelVoucher() {
    const fileInput = document.getElementById('modalHotelImage');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file first');
        return;
    }
    
    // Show loading state
    document.getElementById('modalUploadSection').style.display = 'none';
    document.getElementById('modalLoadingSection').style.display = 'block';
    document.getElementById('modalResultsSection').style.display = 'none';
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('image', file);
    
    // Use the existing API endpoint
    fetch('/booking/api/scan-hotel-voucher', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Hotel voucher analysis result:', data);
        
        // Hide loading
        document.getElementById('modalLoadingSection').style.display = 'none';
        
        if (data.error) {
            alert('Error analyzing voucher: ' + data.error);
            document.getElementById('modalUploadSection').style.display = 'block';
            return;
        }
        
        // Show results
        displayHotelScanResults(data);
        document.getElementById('modalResultsSection').style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('modalLoadingSection').style.display = 'none';
        document.getElementById('modalUploadSection').style.display = 'block';
        alert('Error analyzing voucher: ' + error.message);
    });
}

function displayHotelScanResults(data) {
    // Display basic hotel information
    document.getElementById('extractedHotelName').textContent = data.hotel_name || '-';
    document.getElementById('extractedCheckin').textContent = data.checkin_date || '-';
    document.getElementById('extractedCheckout').textContent = data.checkout_date || '-';
    document.getElementById('extractedConfirmation').textContent = data.confirmation_number || '-';
    document.getElementById('extractedCost').textContent = data.total_cost || '-';
    
    // Display room details
    const roomsContainer = document.getElementById('extractedRoomsContainer');
    roomsContainer.innerHTML = '';
    
    if (data.rooms && data.rooms.length > 0) {
        data.rooms.forEach((room, index) => {
            const roomHtml = `
                <div class="mb-2 p-2 bg-light rounded">
                    <strong>Room ${index + 1}:</strong> ${room.room_type || 'N/A'}<br>
                    <small>
                        <strong>Board:</strong> ${room.board_basis || 'N/A'} |
                        <strong>Guests:</strong> ${room.adults || 0} adults, ${room.children || 0} children<br>
                        <strong>Lead Guest:</strong> ${room.lead_passenger || 'N/A'}
                    </small>
                </div>
            `;
            roomsContainer.insertAdjacentHTML('beforeend', roomHtml);
        });
    } else {
        roomsContainer.innerHTML = '<div class="text-muted">No room details found</div>';
    }
    
    // Store data for form filling
    window.hotelScanData = data;
}

function fillHotelForm() {
    const data = window.hotelScanData;
    if (!data) return;
    
    // Fill basic hotel information
    const hotelNameInput = document.querySelector('input[name="hotel_name"]');
    if (hotelNameInput && data.hotel_name) {
        hotelNameInput.value = data.hotel_name;
    }
    
    const checkinInput = document.querySelector('input[name="from_date"]');
    if (checkinInput && data.checkin_date) {
        checkinInput.value = data.checkin_date;
    }
    
    const checkoutInput = document.querySelector('input[name="to_date"]');
    if (checkoutInput && data.checkout_date) {
        checkoutInput.value = data.checkout_date;
    }
    
    // Fill cost if available
    const costInput = document.querySelector('input[name="cost"]');
    if (costInput && data.total_cost) {
        // Extract numeric value from cost string
        const numericCost = data.total_cost.replace(/[^\d.]/g, '');
        if (numericCost) {
            costInput.value = numericCost;
        }
    }
    
    // Clear existing rooms and create new ones based on scanned data
    if (data.rooms && data.rooms.length > 0) {
        const container = document.getElementById('hotelRoomsContainer');
        
        // Clear all existing rooms
        container.innerHTML = '';
        
        // For each room type detected, create room cards
        data.rooms.forEach((room, index) => {
            // Create room card
            const roomHtml = createRoomHtml(index);
            container.insertAdjacentHTML('beforeend', roomHtml);
            
            // Fill room data immediately
            fillRoomData(index, room);
        });
        
        updateRoomRemoveButtons();
    }

    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('hotelScannerModal'));
    modal.hide();
    
    // Show success message
    alert('Hotel details filled successfully from the voucher!');
}

function fillRoomData(roomIndex, roomData) {
    // Fill room count if available
    const roomCountInput = document.querySelector(`input[name="rooms[${roomIndex}][room_count]"]`);
    if (roomCountInput && roomData.room_count) {
        roomCountInput.value = roomData.room_count;
    }
    
    // Fill room type - try to find exact match or closest match
    const roomTypeSelect = document.querySelector(`select[name="rooms[${roomIndex}][room_type]"]`);
    if (roomTypeSelect && roomData.room_type) {
        const roomType = roomData.room_type.toLowerCase();
        let matchedOption = null;
        
        // Try to find exact or partial match
        for (let option of roomTypeSelect.options) {
            const optionText = option.textContent.toLowerCase();
            if (optionText.includes(roomType) || roomType.includes(optionText.replace(' room', ''))) {
                matchedOption = option.value;
                break;
            }
        }
        
        if (matchedOption) {
            roomTypeSelect.value = matchedOption;
        } else {
            // If no match found, set as "Other" and add a note
            roomTypeSelect.value = 'Other';
        }
    }
    
    // Fill board basis
    const boardSelect = document.querySelector(`select[name="rooms[${roomIndex}][board_basis]"]`);
    if (boardSelect && roomData.board_basis) {
        const boardBasis = roomData.board_basis;
        let matchedBoard = null;
        
        // Map board basis to options
        if (boardBasis.toLowerCase().includes('all inclusive') || boardBasis.toLowerCase().includes('ai')) {
            matchedBoard = 'All Inclusive (AI)';
        } else if (boardBasis.toLowerCase().includes('full board') || boardBasis.toLowerCase().includes('fb')) {
            matchedBoard = 'Full Board (FB)';
        } else if (boardBasis.toLowerCase().includes('half board') || boardBasis.toLowerCase().includes('hb')) {
            matchedBoard = 'Half Board (HB)';
        } else if (boardBasis.toLowerCase().includes('breakfast') || boardBasis.toLowerCase().includes('bb')) {
            matchedBoard = 'Bed & Breakfast (BB)';
        } else if (boardBasis.toLowerCase().includes('room only')) {
            matchedBoard = 'Room Only';
        }
        
        if (matchedBoard) {
            boardSelect.value = matchedBoard;
        }
    }
    
    // Fill guest numbers
    const adultsInput = document.querySelector(`input[name="rooms[${roomIndex}][adults]"]`);
    if (adultsInput && roomData.adults) {
        adultsInput.value = roomData.adults;
    }
    
    const childrenInput = document.querySelector(`input[name="rooms[${roomIndex}][children]"]`);
    if (childrenInput && roomData.children) {
        childrenInput.value = roomData.children;
    }
    
    // Fill lead passenger
    const leadPassengerInput = document.querySelector(`input[name="rooms[${roomIndex}][lead_passenger]"]`);
    if (leadPassengerInput && roomData.lead_passenger) {
        leadPassengerInput.value = roomData.lead_passenger;
    }
}