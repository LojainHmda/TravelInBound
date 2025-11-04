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
            // Service button clicks
            if (e.target.closest('[data-service]')) {
                const button = e.target.closest('[data-service]');
                const serviceType = button.getAttribute('data-service');
                this.openServiceModal(serviceType);
                e.preventDefault();
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
        
        // For hotel and guide, apply to ALL days (no selection needed)
        let targetDates = this.selectedDates;
        if (['hotel', 'guide'].includes(this.currentServiceType)) {
            targetDates = this.getAllItineraryDates();
        }
        
        if (targetDates.length === 0) {
            alert('Please select at least one date by clicking on the itinerary rows.');
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
        
        // Auto-save and reload
        console.log(`${this.currentServiceType} service applied to ${targetDates.length} day(s)`);
        this.autoSave();
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
        
        // Trigger the existing save function
        if (typeof saveItinerary === 'function') {
            saveItinerary();
        } else {
            console.error('saveItinerary function not found');
            // Reload page after a short delay to show changes
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
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
    if (typeof saveItinerary === 'function') {
        saveItinerary();
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
