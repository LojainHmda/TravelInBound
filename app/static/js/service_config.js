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
        const serviceFlagsCell = row.querySelector('td:nth-child(5) .d-flex');
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
            hotel: { class: 'bg-danger', icon: 'fas fa-bed', text: 'Hotel' },
            guide: { class: 'bg-success', icon: 'fas fa-user-tie', text: 'Guide' },
            transport: { class: 'bg-info', icon: 'fas fa-car', text: 'Transport' },
            meal: { class: 'bg-warning text-dark', icon: 'fas fa-utensils', text: 'Meal' },
            airport: { class: 'bg-secondary', icon: 'fas fa-plane', text: 'Airport' }
        };
        
        const config = serviceConfig[serviceType] || serviceConfig.hotel;
        badge.className += ' ' + config.class;
        
        badge.innerHTML = `
            <i class="${config.icon}"></i> ${config.text}
            <button type="button" class="btn-remove-service" onclick="event.stopPropagation(); this.closest('.service-badge-removable').remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        serviceFlagsCell.appendChild(badge);
        
        console.log(`Added ${serviceType} badge to row`);
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

console.log('Service Config JS loaded successfully');