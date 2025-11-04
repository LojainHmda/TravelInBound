// Service Configuration Module - Completely Separated from Templates
console.log('Service Config JS loading...');

class ServiceConfigManager {
    constructor() {
        this.selectedRows = [];
        this.currentServiceType = '';
        this.serviceConfigModal = null;
        
        console.log('ServiceConfigManager initialized');
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.bindEvents());
        } else {
            this.bindEvents();
        }
    }
    
    bindEvents() {
        console.log('Binding service config events...');
        
        // Initialize modal
        const modalElement = document.getElementById('serviceConfigModal');
        if (modalElement) {
            this.serviceConfigModal = new bootstrap.Modal(modalElement);
            console.log('Service modal initialized');
        }
        
        // Bind service button clicks using event delegation
        document.addEventListener('click', (e) => {
            // Service configuration buttons
            if (e.target.closest('[data-service]')) {
                const button = e.target.closest('[data-service]');
                const serviceType = button.getAttribute('data-service');
                console.log('Service button clicked:', serviceType);
                this.showServiceConfigModal(serviceType);
                return;
            }
            
            // Row selection
            if (e.target.closest('.itinerary-row')) {
                const row = e.target.closest('.itinerary-row');
                const rowIndex = row.getAttribute('data-row-index');
                if (rowIndex !== null) {
                    this.selectRow(parseInt(rowIndex));
                }
                return;
            }
            
            // Apply service button
            if (e.target.closest('#applyServiceBtn')) {
                this.applyServiceToDateRange();
                return;
            }
        });
        
        console.log('Event delegation bound successfully');
    }
    
    showServiceConfigModal(serviceType) {
        console.log('Opening service config modal for:', serviceType);
        
        this.currentServiceType = serviceType;
        this.selectedRows = [];
        
        // Reset row selections visually
        document.querySelectorAll('.itinerary-row').forEach(row => {
            row.classList.remove('selected');
        });
        
        // Update modal title
        const titleElement = document.getElementById('serviceTypeTitle');
        if (titleElement) {
            titleElement.textContent = serviceType.charAt(0).toUpperCase() + serviceType.slice(1);
            console.log('Updated title to:', titleElement.textContent);
        } else {
            console.error('Title element not found');
        }
        
        // Hide all service config sections
        document.querySelectorAll('.service-config-section').forEach(section => {
            section.classList.add('d-none');
            console.log('Hidden section:', section.id);
        });
        
        // Show the relevant service config section
        const configSection = document.getElementById(serviceType + 'ServiceConfig');
        if (configSection) {
            configSection.classList.remove('d-none');
            console.log('Showing section:', configSection.id);
        } else {
            console.error('Config section not found:', serviceType + 'ServiceConfig');
        }
        
        // Check modal element exists
        const modalElement = document.getElementById('serviceConfigModal');
        if (modalElement) {
            console.log('Modal element found, classes:', modalElement.className);
        } else {
            console.error('Modal element not found');
        }
        
        // Show modal
        if (this.serviceConfigModal) {
            this.serviceConfigModal.show();
            console.log('Modal shown for service:', serviceType);
            
            // Initialize hotel-specific functionality if it's a hotel service
            if (serviceType === 'hotel') {
                setTimeout(() => {
                    this.initializeHotelFunctionality();
                    // Auto-generate initial room table based on default values
                    regenerateRoomTableFromSummary();
                }, 200);
            }
            
            // Check if modal is actually visible after a short delay
            setTimeout(() => {
                const modalBackdrop = document.querySelector('.modal-backdrop');
                const modalDialog = document.querySelector('#serviceConfigModal .modal-dialog');
                console.log('Modal backdrop exists:', !!modalBackdrop);
                console.log('Modal dialog exists:', !!modalDialog);
                if (modalDialog) {
                    console.log('Modal dialog visible:', modalDialog.offsetHeight > 0);
                }
            }, 100);
        } else {
            console.error('Modal not initialized');
        }
    }
    
    selectRow(index) {
        console.log('Selecting row:', index);
        
        // Only allow row selection when modal is open
        const modalElement = document.getElementById('serviceConfigModal');
        if (!modalElement || !modalElement.classList.contains('show')) {
            return;
        }
        
        const row = document.querySelector(`[data-row-index="${index}"]`);
        if (!row) return;
        
        if (this.selectedRows.includes(index)) {
            // Deselect
            this.selectedRows = this.selectedRows.filter(i => i !== index);
            row.classList.remove('selected');
        } else {
            // Select
            this.selectedRows.push(index);
            row.classList.add('selected');
        }
        
        console.log('Selected rows:', this.selectedRows);
    }
    
    applyServiceToDateRange() {
        console.log('Applying service to date range');
        
        if (!this.currentServiceType) {
            alert('No service type selected');
            return;
        }
        
        // For hotel and guide services, we don't require row selection
        if (!['hotel', 'guide'].includes(this.currentServiceType) && this.selectedRows.length === 0) {
            alert('Please select at least one date from your itinerary by clicking on the rows.');
            return;
        }
        
        // Collect service data based on type
        const serviceData = this.collectServiceData();
        if (!serviceData) {
            alert('Please fill in the required service information.');
            return;
        }
        
        console.log('Service data collected:', serviceData);
        
        // Apply service to rows
        this.applyServiceToRows(serviceData);
        
        // Close modal
        if (this.serviceConfigModal) {
            this.serviceConfigModal.hide();
        }
        
        // Show success message
        const appliedCount = ['hotel', 'guide'].includes(this.currentServiceType) ? 
            document.querySelectorAll('.itinerary-row').length : this.selectedRows.length;
        
        alert(`${this.currentServiceType.charAt(0).toUpperCase() + this.currentServiceType.slice(1)} service added to ${appliedCount} day(s) successfully!`);
    }
    
    collectServiceData() {
        const serviceType = this.currentServiceType;
        
        switch(serviceType) {
            case 'hotel':
                return {
                    hotelName: document.getElementById('hotelName')?.value || '',
                    location: document.getElementById('hotelLocation')?.value || '',
                    checkin: document.getElementById('hotelDefaultCheckin')?.value || '',
                    checkout: document.getElementById('hotelDefaultCheckout')?.value || '',
                    cost: document.getElementById('hotelCost')?.value || 0
                };
                
            case 'transport':
                return {
                    vehicleType: document.getElementById('transportVehicleType')?.value || '',
                    pickupLocation: document.getElementById('transportPickupLocation')?.value || '',
                    dropoffLocation: document.getElementById('transportDropoffLocation')?.value || '',
                    pickupTime: document.getElementById('transportPickupTime')?.value || ''
                };
                
            case 'guide':
                return {
                    guideName: document.getElementById('guideName')?.value || '',
                    language: document.getElementById('guideLanguage')?.value || '',
                    serviceType: document.getElementById('guideServiceType')?.value || '',
                    cost: document.getElementById('guideCost')?.value || 0
                };
                
            case 'meal':
                return {
                    mealType: document.getElementById('mealType')?.value || '',
                    restaurant: document.getElementById('mealRestaurant')?.value || '',
                    location: document.getElementById('mealLocation')?.value || ''
                };
                
            case 'airport':
                return {
                    serviceType: document.getElementById('airportServiceType')?.value || '',
                    flightNumber: document.getElementById('airportFlightNumber')?.value || '',
                    terminal: document.getElementById('airportTerminal')?.value || ''
                };
                
            case 'arrival':
                return {
                    arrivalPoint: document.getElementById('itinerary_arrival_point')?.value || '',
                    arrivalTime: document.getElementById('itinerary_arrival_time')?.value || '',
                    departurePoint: document.getElementById('itinerary_departure_point')?.value || '',
                    departureTime: document.getElementById('itinerary_departure_time')?.value || ''
                };
                
            default:
                return null;
        }
    }
    
    applyServiceToRows(serviceData) {
        const serviceType = this.currentServiceType;
        
        // For hotel and guide services, apply to all rows in date range
        if (['hotel', 'guide'].includes(serviceType)) {
            document.querySelectorAll('.itinerary-row').forEach((row, index) => {
                this.addServiceBadgeToRow(row, serviceType, serviceData);
            });
        } else {
            // Apply to selected rows only
            this.selectedRows.forEach(rowIndex => {
                const row = document.querySelector(`[data-row-index="${rowIndex}"]`);
                if (row) {
                    this.addServiceBadgeToRow(row, serviceType, serviceData);
                }
            });
        }
    }
    
    addServiceBadgeToRow(row, serviceType, serviceData) {
        const serviceFlagsCell = row.querySelector('td:nth-child(6) .d-flex');
        if (!serviceFlagsCell) return;
        
        // Remove existing badge of same type
        const existingBadge = serviceFlagsCell.querySelector(`[data-service="${serviceType}"]`);
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Create new service badge
        const badge = document.createElement('span');
        badge.className = `badge service-badge-removable`;
        badge.setAttribute('data-service', serviceType);
        
        // Set badge color and icon based on service type
        const serviceConfig = {
            hotel: { class: 'bg-danger', icon: 'fas fa-bed', text: 'Hotel', flag: 'flag_hotel' },
            guide: { class: 'bg-success', icon: 'fas fa-user-tie', text: 'Guide', flag: 'flag_guide' },
            transport: { class: 'bg-info', icon: 'fas fa-car', text: 'Transport', flag: 'flag_transport' },
            meal: { class: 'bg-warning text-dark', icon: 'fas fa-utensils', text: 'Meal', flag: 'flag_meal' },
            airport: { class: 'bg-secondary', icon: 'fas fa-plane', text: 'Airport', flag: 'flag_airport' },
            arrival: { class: 'bg-primary', icon: 'fas fa-plane', text: 'Arrival/Departure', flag: 'flag_airport' }
        };
        
        const config = serviceConfig[serviceType] || serviceConfig.hotel;
        badge.className += ' ' + config.class;
        
        badge.innerHTML = `
            <i class="${config.icon}"></i> ${config.text}
            <button type="button" class="btn-remove-service" onclick="event.stopPropagation(); removeServiceFlag(this, '${config.flag}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        serviceFlagsCell.appendChild(badge);
        
        // Set the hidden flag input
        const rowIndex = row.getAttribute('data-row-index');
        const flagInputName = `flag_${serviceType}_${rowIndex}`;
        const flagInput = document.querySelector(`input[name="${flagInputName}"]`);
        if (flagInput) {
            flagInput.value = '1';
            console.log(`Set flag input ${flagInputName} to 1`);
        } else {
            console.error(`Flag input not found: ${flagInputName}`);
        }
        
        console.log(`Added ${serviceType} badge to row and set ${config.flag} flag`);
    }
    
    // Hotel-specific functionality
    initializeHotelFunctionality() {
        // Hotel autocomplete initialization
        const hotelNameInput = document.getElementById('hotelName');
        if (hotelNameInput) {
            this.setupHotelAutocomplete(hotelNameInput);
        }
        
        // Initialize room distribution functionality
        updateRoomDistribution();
    }
    
    setupHotelAutocomplete(inputElement) {
        // Create autocomplete container
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'autocomplete-suggestions';
        suggestionsContainer.style.cssText = `
            display: none;
            position: absolute;
            z-index: 1050;
            background: white;
            border: 1px solid #ddd;
            max-height: 200px;
            overflow-y: auto;
            width: ${inputElement.offsetWidth}px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 4px;
        `;
        
        inputElement.parentNode.insertBefore(suggestionsContainer, inputElement.nextSibling);
        
        inputElement.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            
            if (query.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            // Check if HOTEL_NAMES exists (from hotel_autocomplete_data.js)
            if (typeof HOTEL_NAMES !== 'undefined') {
                const suggestions = HOTEL_NAMES.filter(hotel => 
                    hotel.name.toLowerCase().includes(query)
                ).slice(0, 8);
                
                if (suggestions.length > 0) {
                    suggestionsContainer.innerHTML = suggestions.map(hotel => 
                        `<div class="suggestion-item" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;" 
                             onmouseover="this.style.backgroundColor='#f8f9fa'" 
                             onmouseout="this.style.backgroundColor='white'"
                             onclick="document.getElementById('hotelName').value='${hotel.name}'; this.parentNode.style.display='none';">
                            ${hotel.name}
                        </div>`
                    ).join('');
                    suggestionsContainer.style.display = 'block';
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!inputElement.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
    }
}

// Initialize the service config manager
let serviceManager;

// Ensure initialization happens after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        serviceManager = new ServiceConfigManager();
        console.log('ServiceConfigManager initialized on DOMContentLoaded');
    });
} else {
    serviceManager = new ServiceConfigManager();
    console.log('ServiceConfigManager initialized immediately');
}

// Global functions for hotel room management (for onclick handlers)
function addHotelRoomToTable() {
    const tableBody = document.getElementById('hotelRoomsTableBody');
    if (!tableBody) return;
    
    const roomCount = tableBody.querySelectorAll('tr').length;
    const roomIndex = roomCount;
    
    const newRow = document.createElement('tr');
    newRow.className = 'hotel-room-row';
    newRow.innerHTML = `
        <td><strong class="text-primary">Room ${roomIndex + 1}</strong></td>
        <td>
            <select name="rooms[${roomIndex}][room_category]" class="form-control" onchange="updateRoomDistribution()">
                <option value="Single Room">Single</option>
                <option value="Double Room">Double</option>
                <option value="Triple Room">Triple</option>
                <option value="Other">Other</option>
            </select>
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][hotel_room_option]" class="form-control" placeholder="Premium, Premier Sea View">
        </td>
        <td>
            <select name="rooms[${roomIndex}][board_basis]" class="form-control">
                <option value="Room Only">Room Only</option>
                <option value="Bed & Breakfast">Bed & Breakfast</option>
                <option value="Half Board">Half Board (Breakfast + Dinner)</option>
                <option value="Full Board">Full Board (All Meals)</option>
                <option value="All Inclusive">All Inclusive</option>
                <option value="Ultra All Inclusive">Ultra All Inclusive</option>
            </select>
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][dietary_requirements]" class="form-control" placeholder="Vegetarian, Halal, Gluten-free">
        </td>
        <td>
            <input type="date" name="rooms[${roomIndex}][check_in]" class="form-control">
        </td>
        <td>
            <input type="date" name="rooms[${roomIndex}][check_out]" class="form-control">
        </td>
        <td>
            <input type="number" name="rooms[${roomIndex}][adults]" class="form-control" value="1" min="1" max="8">
        </td>
        <td>
            <input type="number" name="rooms[${roomIndex}][children]" class="form-control" value="0" min="0" max="8">
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][lead_passenger]" class="form-control" placeholder="Lead passenger name" style="min-width: 180px;">
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeHotelTableRoom(this)">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tableBody.appendChild(newRow);
    updateRoomDistribution();
    console.log('Hotel room added');
}

function removeHotelTableRoom(button) {
    const row = button.closest('tr');
    const tableBody = document.getElementById('hotelRoomsTableBody');
    
    if (tableBody.querySelectorAll('tr').length > 1) {
        row.remove();
        
        // Renumber remaining rooms
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const roomNumber = row.querySelector('td strong');
            if (roomNumber) {
                roomNumber.textContent = `Room ${index + 1}`;
            }
            
            // Update input names
            const inputs = row.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.name && input.name.includes('rooms[')) {
                    input.name = input.name.replace(/rooms\[\d+\]/, `rooms[${index}]`);
                }
            });
        });
        
        updateRoomDistribution();
        console.log('Hotel room removed');
    }
}

function updateRoomDistribution() {
    const rows = document.querySelectorAll('.hotel-room-row');
    let singleCount = 0, doubleCount = 0, tripleCount = 0, otherCount = 0;
    
    rows.forEach(row => {
        const categorySelect = row.querySelector('select[name*="room_category"]');
        if (categorySelect) {
            const value = categorySelect.value;
            if (value === 'Single Room') singleCount++;
            else if (value === 'Double Room') doubleCount++;
            else if (value === 'Triple Room') tripleCount++;
            else if (value && value !== '') otherCount++;
        }
    });
    
    // Update distribution summary
    const singleInput = document.getElementById('hotelSingleRooms');
    const doubleInput = document.getElementById('hotelDoubleRooms');
    const tripleInput = document.getElementById('hotelTripleRooms');
    const otherInput = document.getElementById('hotelOtherRooms');
    
    if (singleInput) singleInput.value = singleCount;
    if (doubleInput) doubleInput.value = doubleCount;
    if (tripleInput) tripleInput.value = tripleCount;
    if (otherInput) otherInput.value = otherCount;
    
    console.log(`Room distribution updated: ${singleCount} single, ${doubleCount} double, ${tripleCount} triple, ${otherCount} other`);
}

// Master room configuration function
function regenerateRoomTable() {
    const singleCount = parseInt(document.getElementById('masterSingleRooms')?.value || 0);
    const doubleCount = parseInt(document.getElementById('masterDoubleRooms')?.value || 0);
    const tripleCount = parseInt(document.getElementById('masterTripleRooms')?.value || 0);
    const otherCount = parseInt(document.getElementById('masterOtherRooms')?.value || 0);
    
    const tableBody = document.getElementById('hotelRoomsTableBody');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    let roomIndex = 0;
    
    // Add single rooms
    for (let i = 0; i < singleCount; i++) {
        addRoomRow(roomIndex++, 'Single Room');
    }
    
    // Add double rooms
    for (let i = 0; i < doubleCount; i++) {
        addRoomRow(roomIndex++, 'Double Room');
    }
    
    // Add triple rooms
    for (let i = 0; i < tripleCount; i++) {
        addRoomRow(roomIndex++, 'Triple Room');
    }
    
    // Add other rooms
    for (let i = 0; i < otherCount; i++) {
        addRoomRow(roomIndex++, 'Other');
    }
    
    updateRoomDistribution();
    console.log(`Generated ${roomIndex} rooms: ${singleCount} single, ${doubleCount} double, ${tripleCount} triple, ${otherCount} other`);
}

// Helper function to add a room row with specific type
function addRoomRow(roomIndex, roomType) {
    const tableBody = document.getElementById('hotelRoomsTableBody');
    if (!tableBody) return;
    
    const newRow = document.createElement('tr');
    newRow.className = 'hotel-room-row';
    
    // Set default adults based on room type
    let defaultAdults = 1;
    if (roomType === 'Double Room') defaultAdults = 2;
    if (roomType === 'Triple Room') defaultAdults = 3;
    
    newRow.innerHTML = `
        <td><strong class="text-primary">Room ${roomIndex + 1}</strong></td>
        <td>
            <select name="rooms[${roomIndex}][room_category]" class="form-control" onchange="updateRoomDistribution()">
                <option value="Single Room" ${roomType === 'Single Room' ? 'selected' : ''}>Single</option>
                <option value="Double Room" ${roomType === 'Double Room' ? 'selected' : ''}>Double</option>
                <option value="Triple Room" ${roomType === 'Triple Room' ? 'selected' : ''}>Triple</option>
                <option value="Other" ${roomType === 'Other' ? 'selected' : ''}>Other</option>
            </select>
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][hotel_room_option]" class="form-control" placeholder="Premium, Premier Sea View">
        </td>
        <td>
            <select name="rooms[${roomIndex}][board_basis]" class="form-control">
                <option value="Room Only">Room Only</option>
                <option value="Bed & Breakfast" selected>Bed & Breakfast</option>
                <option value="Half Board">Half Board (Breakfast + Dinner)</option>
                <option value="Full Board">Full Board (All Meals)</option>
                <option value="All Inclusive">All Inclusive</option>
                <option value="Ultra All Inclusive">Ultra All Inclusive</option>
            </select>
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][dietary_requirements]" class="form-control" placeholder="Vegetarian, Halal, Gluten-free">
        </td>
        <td>
            <input type="date" name="rooms[${roomIndex}][check_in]" class="form-control">
        </td>
        <td>
            <input type="date" name="rooms[${roomIndex}][check_out]" class="form-control">
        </td>
        <td>
            <input type="number" name="rooms[${roomIndex}][adults]" class="form-control" value="${defaultAdults}" min="1" max="8">
        </td>
        <td>
            <input type="number" name="rooms[${roomIndex}][children]" class="form-control" value="0" min="0" max="8">
        </td>
        <td>
            <input type="text" name="rooms[${roomIndex}][lead_passenger]" class="form-control" placeholder="Lead passenger name" style="min-width: 180px;">
        </td>
        <td>
            <span class="text-muted"><small>Use Master Config</small></span>
        </td>
    `;
    
    tableBody.appendChild(newRow);
}

// Function to sync master config with room distribution summary
function updateMasterFromSummary() {
    const single = document.getElementById('hotelSingleRooms')?.value || 0;
    const double = document.getElementById('hotelDoubleRooms')?.value || 0;
    const triple = document.getElementById('hotelTripleRooms')?.value || 0;
    const other = document.getElementById('hotelOtherRooms')?.value || 0;
    
    // Update master config inputs if they exist
    if (document.getElementById('masterSingleRooms')) {
        document.getElementById('masterSingleRooms').value = single;
    }
    if (document.getElementById('masterDoubleRooms')) {
        document.getElementById('masterDoubleRooms').value = double;
    }
    if (document.getElementById('masterTripleRooms')) {
        document.getElementById('masterTripleRooms').value = triple;
    }
    if (document.getElementById('masterOtherRooms')) {
        document.getElementById('masterOtherRooms').value = other;
    }
}

// Primary function to generate room table from the summary (main controls)
function regenerateRoomTableFromSummary() {
    const singleCount = parseInt(document.getElementById('hotelSingleRooms')?.value || 0);
    const doubleCount = parseInt(document.getElementById('hotelDoubleRooms')?.value || 0);
    const tripleCount = parseInt(document.getElementById('hotelTripleRooms')?.value || 0);
    const otherCount = parseInt(document.getElementById('hotelOtherRooms')?.value || 0);
    
    const tableBody = document.getElementById('hotelRoomsTableBody');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    let roomIndex = 0;
    
    // Add single rooms
    for (let i = 0; i < singleCount; i++) {
        addRoomRow(roomIndex++, 'Single Room');
    }
    
    // Add double rooms
    for (let i = 0; i < doubleCount; i++) {
        addRoomRow(roomIndex++, 'Double Room');
    }
    
    // Add triple rooms
    for (let i = 0; i < tripleCount; i++) {
        addRoomRow(roomIndex++, 'Triple Room');
    }
    
    // Add other rooms
    for (let i = 0; i < otherCount; i++) {
        addRoomRow(roomIndex++, 'Other');
    }
    
    // Update master config to match
    updateMasterFromSummary();
    
    console.log(`Generated ${roomIndex} rooms from summary: ${singleCount} single, ${doubleCount} double, ${tripleCount} triple, ${otherCount} other`);
}

console.log('Service Config JS loaded successfully');