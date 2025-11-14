// Service Configuration - Simplified and Reliable
console.log('Service Config JS loading...');

class ServiceConfigManager {
    constructor() {
        this.currentServiceType = '';
        this.serviceConfigModal = null;
        this.selectedDates = []; // Array of date strings
        
        console.log('ServiceConfigManager initialized');
        this.init();
    }
    
    init() {
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
        
        // Event delegation for all clicks
        document.addEventListener('click', (e) => {
            // Service button clicks - check for service-icon-button class specifically
            if (e.target.closest('.service-icon-button') || e.target.closest('[data-service]')) {
                const button = e.target.closest('.service-icon-button') || e.target.closest('[data-service]');
                const serviceType = button.getAttribute('data-service');
                console.log('SERVICE BUTTON CLICKED:', serviceType);
                this.openServiceModal(serviceType);
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            // Row selection (only when modal is open)
            if (e.target.closest('.itinerary-row') && this.isModalOpen()) {
                const row = e.target.closest('.itinerary-row');
                const dateStr = row.querySelector('input[name="date[]"]')?.value;
                if (dateStr) {
                    this.toggleDateSelection(dateStr, row);
                }
                e.stopPropagation();
                return;
            }
            
            // Apply service button
            if (e.target.closest('#applyServiceBtn')) {
                this.applyService();
                e.preventDefault();
                return;
            }
        });
        
        console.log('Event delegation bound successfully');
    }
    
    isModalOpen() {
        const modalElement = document.getElementById('serviceConfigModal');
        return modalElement && modalElement.classList.contains('show');
    }
    
    openServiceModal(serviceType) {
        console.log('Opening service modal for:', serviceType);
        
        this.currentServiceType = serviceType;
        this.selectedDates = [];
        
        // Clear all row selections visually
        document.querySelectorAll('.itinerary-row').forEach(row => {
            row.classList.remove('selected');
        });
        
        // Update modal title
        const titleElement = document.getElementById('serviceTypeTitle');
        if (titleElement) {
            titleElement.textContent = serviceType.charAt(0).toUpperCase() + serviceType.slice(1);
        }
        
        // Hide all service config sections
        document.querySelectorAll('.service-config-section').forEach(section => {
            section.classList.add('d-none');
        });
        
        // Show the relevant service config section
        const configSection = document.getElementById(serviceType + 'ServiceConfig');
        if (configSection) {
            configSection.classList.remove('d-none');
        }
        
        // Show modal
        if (this.serviceConfigModal) {
            this.serviceConfigModal.show();
            
            // Initialize hotel-specific functionality
            if (serviceType === 'hotel') {
                setTimeout(() => {
                    if (typeof regenerateRoomTableFromSummary === 'function') {
                        regenerateRoomTableFromSummary();
                    }
                }, 200);
            }
        }
    }
    
    toggleDateSelection(dateStr, row) {
        const index = this.selectedDates.indexOf(dateStr);
        
        if (index > -1) {
            // Deselect
            this.selectedDates.splice(index, 1);
            row.classList.remove('selected');
        } else {
            // Select
            this.selectedDates.push(dateStr);
            row.classList.add('selected');
        }
        
        console.log('Selected dates:', this.selectedDates);
    }
    
    applyService() {
        console.log('Applying service:', this.currentServiceType);
        
        if (!this.currentServiceType) {
            alert('No service type selected');
            return;
        }
        
        // For transport, apply to dates between from/to in transport form
        if (this.currentServiceType === 'transport') {
            console.log('Transport service - applying to date range');
            
            // Get the transport from/to dates from the form
            const fromDateInputs = document.querySelectorAll('input[name="transport_from_date[]"]');
            const toDateInputs = document.querySelectorAll('input[name="transport_to_date[]"]');
            
            // Apply transport flag to all dates between from/to dates
            for (let i = 0; i < fromDateInputs.length; i++) {
                const fromDate = fromDateInputs[i]?.value;
                const toDate = toDateInputs[i]?.value;
                
                if (fromDate && toDate) {
                    // Get all itinerary dates within this range
                    const datesInRange = this.getDatesInRange(fromDate, toDate);
                    datesInRange.forEach(dateStr => {
                        this.setServiceFlag(dateStr, 'transport', true);
                    });
                }
            }
            
            if (this.serviceConfigModal) {
                this.serviceConfigModal.hide();
            }
            this.autoSaveOnly();
            return;
        }
        
        // Initialize targetDates variable
        let targetDates = this.selectedDates;
        
        // For hotel, collect and save hotel data first
        if (this.currentServiceType === 'hotel') {
            console.log('Collecting hotel configuration data...');
            
            // Collect hotel room data
            const hotelData = this.collectHotelData();
            if (hotelData) {
                // Save hotel data via API
                this.saveHotelData(hotelData);
            }
            
            // Apply hotel flag to all dates
            targetDates = this.getAllItineraryDates();
        }
        
        // For guide, apply to ALL days (no selection needed)
        if (this.currentServiceType === 'guide') {
            targetDates = this.getAllItineraryDates();
        }
        
        // Only show date selection alert for meal and airport services
        if (targetDates.length === 0) {
            if (['meal', 'airport'].includes(this.currentServiceType)) {
                alert('Please select at least one date by clicking on the itinerary rows.');
            }
            return;
        }
        
        console.log('Applying to dates:', targetDates);
        
        // Apply the service flag to each selected date
        targetDates.forEach(dateStr => {
            this.setServiceFlag(dateStr, this.currentServiceType, true);
        });
        
        // Close modal
        if (this.serviceConfigModal) {
            this.serviceConfigModal.hide();
        }
        
        // Auto-save ONLY (no reload) to preserve multi-hotel DOM state
        console.log(`${this.currentServiceType} service applied to ${targetDates.length} day(s)`);
        this.autoSaveOnly();
    }
    
    getDatesInRange(fromDateStr, toDateStr) {
        const dates = [];
        const fromDate = new Date(fromDateStr);
        const toDate = new Date(toDateStr);
        
        // Get all itinerary dates
        document.querySelectorAll('input[name="date[]"]').forEach(input => {
            if (input.value) {
                const date = new Date(input.value);
                // Check if this date is within the range (inclusive)
                if (date >= fromDate && date <= toDate) {
                    dates.push(input.value);
                }
            }
        });
        
        console.log(`Found ${dates.length} dates in range ${fromDateStr} to ${toDateStr}`);
        return dates;
    }
    
    getAllItineraryDates() {
        const dates = [];
        document.querySelectorAll('input[name="date[]"]').forEach(input => {
            if (input.value) {
                dates.push(input.value);
            }
        });
        return dates;
    }
    
    setServiceFlag(dateStr, serviceType, value) {
        console.log(`Setting ${serviceType} flag for date ${dateStr} to ${value}`);
        
        // Find the row with this date
        const rows = document.querySelectorAll('.itinerary-row');
        rows.forEach(row => {
            const dateInput = row.querySelector('input[name="date[]"]');
            if (dateInput && dateInput.value === dateStr) {
                // Find the hidden flag input
                const rowIndex = Array.from(rows).indexOf(row);
                const flagInput = document.querySelector(`input[name="flag_${serviceType}_${rowIndex}"]`);
                
                console.log(`Row ${rowIndex}, Flag input:`, flagInput);
                
                if (flagInput) {
                    flagInput.value = value ? '1' : '';
                    console.log(`Set flag_${serviceType}_${rowIndex} to "${flagInput.value}"`);
                    
                    // Update visual badge
                    this.updateServiceBadge(row, serviceType, value);
                } else {
                    console.error(`Flag input not found: flag_${serviceType}_${rowIndex}`);
                }
            }
        });
    }
    
    updateServiceBadge(row, serviceType, shouldShow) {
        const serviceFlagsCell = row.querySelector('td:nth-child(6) .d-flex');
        if (!serviceFlagsCell) return;
        
        // Remove existing badge of same type
        const existingBadge = serviceFlagsCell.querySelector(`[data-service="${serviceType}"]`);
        if (existingBadge) {
            existingBadge.remove();
        }
        
        if (!shouldShow) return;
        
        // Add new badge
        const serviceConfig = {
            hotel: { class: 'bg-danger', icon: 'fas fa-bed', text: 'Hotel' },
            guide: { class: 'bg-success', icon: 'fas fa-user-tie', text: 'Guide' },
            transport: { class: 'bg-info', icon: 'fas fa-car', text: 'Transport' },
            meal: { class: 'bg-warning text-dark', icon: 'fas fa-utensils', text: 'Meal' },
            airport: { class: 'bg-secondary', icon: 'fas fa-plane', text: 'Airport' }
        };
        
        const config = serviceConfig[serviceType] || serviceConfig.hotel;
        
        const badge = document.createElement('span');
        badge.className = `badge ${config.class} service-badge-removable`;
        badge.setAttribute('data-service', serviceType);
        badge.innerHTML = `
            <i class="${config.icon}"></i> ${config.text}
            <button type="button" class="btn-remove-service" onclick="removeServiceFromRow(this, '${serviceType}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        serviceFlagsCell.appendChild(badge);
        console.log(`Added ${serviceType} badge to row`);
    }
    
    autoSave() {
        console.log('Auto-saving itinerary...');
        
        // Get the form and trigger submission
        const form = document.getElementById('itineraryForm');
        if (form) {
            // Create a synthetic submit event
            const submitEvent = new Event('submit', {
                bubbles: true,
                cancelable: true
            });
            
            // Dispatch the event which will trigger saveItinerary(event)
            form.dispatchEvent(submitEvent);
        } else {
            console.error('Itinerary form not found');
            // Reload page as fallback
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }
    
    autoSaveOnly() {
        console.log('Auto-saving itinerary without reload...');
        
        // Get the form and trigger submission
        const form = document.getElementById('itineraryForm');
        if (form) {
            // Create a synthetic submit event
            const submitEvent = new Event('submit', {
                bubbles: true,
                cancelable: true
            });
            
            // Dispatch the event which will trigger saveItinerary(event)
            form.dispatchEvent(submitEvent);
            
            // Show success message without reload
            console.log('Itinerary saved! Modal will stay open to preserve multi-hotel state.');
        } else {
            console.log('Itinerary form not found, skipping auto-save');
        }
    }
    
    collectHotelData() {
        console.log('Collecting hotel data from form...');
        
        const hotels = [];
        const hotelCards = document.querySelectorAll('.hotel-card');
        
        hotelCards.forEach((card, hotelIndex) => {
            const hotelData = {
                hotel_index: hotelIndex,
                hotel_name: card.querySelector('[name*="hotel_name"]')?.value || '',
                hotel_single_rooms: parseInt(card.querySelector('[name*="hotel_single_rooms"]')?.value || 0),
                hotel_double_rooms: parseInt(card.querySelector('[name*="hotel_double_rooms"]')?.value || 0),
                hotel_triple_rooms: parseInt(card.querySelector('[name*="hotel_triple_rooms"]')?.value || 0),
                hotel_other_rooms: parseInt(card.querySelector('[name*="hotel_other_rooms"]')?.value || 0),
                rooms: []
            };
            
            // Collect room details
            const roomRows = card.querySelectorAll('.hotel-room-row');
            roomRows.forEach((row, roomIndex) => {
                const roomData = {
                    room_category: row.querySelector(`[name="rooms[${roomIndex}][room_category]"]`)?.value || '',
                    hotel_room_option: row.querySelector(`[name="rooms[${roomIndex}][hotel_room_option]"]`)?.value || '',
                    board_basis: row.querySelector(`[name="rooms[${roomIndex}][board_basis]"]`)?.value || '',
                    dietary_requirements: row.querySelector(`[name="rooms[${roomIndex}][dietary_requirements]"]`)?.value || '',
                    check_in: row.querySelector(`[name="rooms[${roomIndex}][check_in]"]`)?.value || '',
                    check_out: row.querySelector(`[name="rooms[${roomIndex}][check_out]"]`)?.value || '',
                    adults: parseInt(row.querySelector(`[name="rooms[${roomIndex}][adults]"]`)?.value || 0),
                    children: parseInt(row.querySelector(`[name="rooms[${roomIndex}][children]"]`)?.value || 0),
                    lead_passenger: row.querySelector(`[name="rooms[${roomIndex}][lead_passenger]"]`)?.value || ''
                };
                hotelData.rooms.push(roomData);
            });
            
            hotels.push(hotelData);
        });
        
        console.log('Collected hotel data:', hotels);
        return hotels;
    }
    
    saveHotelData(hotelData) {
        console.log('Saving hotel data to backend...');
        
        // Get request ID from URL or page
        const pathParts = window.location.pathname.split('/');
        const requestId = pathParts[pathParts.indexOf('inbound') + 1];
        
        if (!requestId) {
            console.error('Request ID not found');
            return;
        }
        
        // Save via API
        fetch(`/inbound/api/${requestId}/save-hotels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content')
            },
            body: JSON.stringify({ hotels: hotelData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Hotels saved successfully');
            } else {
                console.error('Error saving hotels:', data.message);
            }
        })
        .catch(error => {
            console.error('Error saving hotels:', error);
        });
    }
}

// Global function to remove service from a row
function removeServiceFromRow(button, serviceType) {
    const row = button.closest('.itinerary-row');
    if (!row) return;
    
    // Find row index
    const rows = document.querySelectorAll('.itinerary-row');
    const rowIndex = Array.from(rows).indexOf(row);
    
    // Clear the flag
    const flagInput = document.querySelector(`input[name="flag_${serviceType}_${rowIndex}"]`);
    if (flagInput) {
        flagInput.value = '';
        console.log(`Cleared flag_${serviceType}_${rowIndex}`);
    }
    
    // Remove badge
    const badge = button.closest('.badge');
    if (badge) {
        badge.remove();
    }
    
    // Auto-save
    const form = document.getElementById('itineraryForm');
    if (form) {
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(submitEvent);
    }
}

// Initialize the service config manager
let serviceManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        serviceManager = new ServiceConfigManager();
        console.log('ServiceConfigManager initialized on DOMContentLoaded');
    });
} else {
    serviceManager = new ServiceConfigManager();
    console.log('ServiceConfigManager initialized immediately');
}

console.log('Service Config JS loaded successfully');
