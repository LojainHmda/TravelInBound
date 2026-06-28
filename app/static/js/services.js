/**
 * Services Management Module for Inbound Tour Operator
 * Handles service auto-generation, synchronization, and locking
 */

class ServicesManager {
    constructor(requestId) {
        this.requestId = requestId;
        this.services = {
            hotels: [],
            transports: [],
            meals: [],
            guides: []
        };
        this.init();
    }

    init() {
        this.loadServices();
        this.bindEvents();
    }

    bindEvents() {
        // Service form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('service-form')) {
                e.preventDefault();
                this.handleServiceFormSubmit(e.target);
            }
        });
    }

    async loadServices() {
        try {
            const response = await fetch(`/inbound/api/${this.requestId}/services`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.services = data;
            this.renderServiceSections();
        } catch (error) {
            console.error('Error loading services:', error);
        }
    }

    renderServiceSections() {
        this.renderHotels();
        this.renderTransports();
        this.renderMeals();
        this.renderGuides();
    }

    renderHotels() {
        const container = document.getElementById('hotelsContainer');
        if (!container) return;

        container.innerHTML = '';
        
        this.services.hotels.forEach((hotel, index) => {
            const hotelCard = this.createHotelCard(hotel, index);
            container.appendChild(hotelCard);
        });
    }

    createHotelCard(hotel, index) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-bed text-primary"></i>
                    ${hotel.hotel_name || 'Hotel Service'}
                </h6>
                <div>
                    ${hotel.is_locked ? '<span class="badge bg-warning">Locked</span>' : ''}
                    <span class="badge bg-${this.getStatusBadgeClass(hotel.status)}">${hotel.status}</span>
                </div>
            </div>
            <div class="card-body">
                <form class="service-form" data-service-type="hotel" data-service-id="${hotel.id}">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Hotel Name</label>
                                <input type="text" class="form-control" name="hotel_name" 
                                       value="${hotel.hotel_name || ''}" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="location" 
                                       value="${hotel.location || ''}" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Check-in</label>
                                <input type="date" class="form-control" name="check_in_date" 
                                       value="${hotel.check_in_date}" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Check-out</label>
                                <input type="date" class="form-control" name="check_out_date" 
                                       value="${hotel.check_out_date}" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Nights</label>
                                <input type="number" class="form-control" name="nights" 
                                       value="${hotel.nights}" min="1" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Room Type</label>
                                <input type="text" class="form-control" name="room_type" 
                                       value="${hotel.room_type || ''}" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Meal Plan</label>
                                <select class="form-select" name="meal_plan" ${hotel.is_locked ? 'disabled' : ''}>
                                    <option value="BB" ${hotel.meal_plan === 'BB' ? 'selected' : ''}>Bed & Breakfast</option>
                                    <option value="HB" ${hotel.meal_plan === 'HB' ? 'selected' : ''}>Half Board</option>
                                    <option value="FB" ${hotel.meal_plan === 'FB' ? 'selected' : ''}>Full Board</option>
                                    <option value="AI" ${hotel.meal_plan === 'AI' ? 'selected' : ''}>All Inclusive</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Total Cost</label>
                                <input type="number" class="form-control" name="total_cost"
                                       value="${hotel.total_cost}" step="0.01" min="0" ${hotel.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Currency</label>
                                <select class="form-select" name="currency" ${hotel.is_locked ? 'disabled' : ''}>
                                    <option value="USD" ${hotel.currency === 'USD' ? 'selected' : ''}>USD</option>
                                    <option value="EUR" ${hotel.currency === 'EUR' ? 'selected' : ''}>EUR</option>
                                    <option value="JOD" ${hotel.currency === 'JOD' ? 'selected' : ''}>JOD</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    ${!hotel.is_locked ? `
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="servicesManager.deleteService('hotel', ${hotel.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                            <button type="submit" class="btn btn-primary btn-sm">
                                <i class="fas fa-save"></i> Save Hotel
                            </button>
                        </div>
                    ` : ''}
                </form>
            </div>
        `;
        return card;
    }

    renderTransports() {
        const container = document.getElementById('transportsContainer');
        if (!container) return;

        container.innerHTML = '';
        
        this.services.transports.forEach((transport, index) => {
            const transportCard = this.createTransportCard(transport, index);
            container.appendChild(transportCard);
        });
    }

    createTransportCard(transport, index) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-${transport.is_airport_transfer ? 'plane' : 'car'} text-info"></i>
                    ${transport.vehicle_type || 'Transport Service'}
                    ${transport.is_airport_transfer ? ' (Airport)' : ''}
                </h6>
                <div>
                    ${transport.is_locked ? '<span class="badge bg-warning">Locked</span>' : ''}
                    <span class="badge bg-${this.getStatusBadgeClass(transport.status)}">${transport.status}</span>
                </div>
            </div>
            <div class="card-body">
                <form class="service-form" data-service-type="transport" data-service-id="${transport.id}">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Date</label>
                                <input type="date" class="form-control" name="date" 
                                       value="${transport.date}" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Vehicle Type</label>
                                <input type="text" class="form-control" name="vehicle_type" 
                                       value="${transport.vehicle_type || ''}" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Pickup Time</label>
                                <input type="time" class="form-control" name="pickup_time" 
                                       value="${transport.pickup_time || ''}" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Pickup Location</label>
                                <input type="text" class="form-control" name="pickup_location" 
                                       value="${transport.pickup_location || ''}" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Dropoff Location</label>
                                <input type="text" class="form-control" name="dropoff_location" 
                                       value="${transport.dropoff_location || ''}" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="is_airport_transfer" 
                                           ${transport.is_airport_transfer ? 'checked' : ''} ${transport.is_locked ? 'disabled' : ''}>
                                    <label class="form-check-label">Airport Transfer</label>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Cost</label>
                                <input type="number" class="form-control" name="cost" 
                                       value="${transport.cost}" step="0.01" min="0" ${transport.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">Currency</label>
                                <select class="form-select" name="currency" ${transport.is_locked ? 'disabled' : ''}>
                                    <option value="USD" ${transport.currency === 'USD' ? 'selected' : ''}>USD</option>
                                    <option value="EUR" ${transport.currency === 'EUR' ? 'selected' : ''}>EUR</option>
                                    <option value="JOD" ${transport.currency === 'JOD' ? 'selected' : ''}>JOD</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    ${!transport.is_locked ? `
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="servicesManager.deleteService('transport', ${transport.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                            <button type="submit" class="btn btn-primary btn-sm">
                                <i class="fas fa-save"></i> Save Transport
                            </button>
                        </div>
                    ` : ''}
                </form>
            </div>
        `;
        return card;
    }

    renderMeals() {
        const container = document.getElementById('mealsContainer');
        if (!container) return;

        container.innerHTML = '';
        
        this.services.meals.forEach((meal, index) => {
            const mealCard = this.createMealCard(meal, index);
            container.appendChild(mealCard);
        });
    }

    createMealCard(meal, index) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-utensils text-warning"></i>
                    ${meal.meal_type || 'Meal Service'} - ${meal.restaurant || 'Restaurant'}
                </h6>
                <div>
                    ${meal.is_locked ? '<span class="badge bg-warning">Locked</span>' : ''}
                    <span class="badge bg-${this.getStatusBadgeClass(meal.status)}">${meal.status}</span>
                </div>
            </div>
            <div class="card-body">
                <form class="service-form" data-service-type="meal" data-service-id="${meal.id}">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Date</label>
                                <input type="date" class="form-control" name="date" 
                                       value="${meal.date}" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Meal Type</label>
                                <select class="form-select" name="meal_type" ${meal.is_locked ? 'disabled' : ''}>
                                    <option value="Breakfast" ${meal.meal_type === 'Breakfast' ? 'selected' : ''}>Breakfast</option>
                                    <option value="Lunch" ${meal.meal_type === 'Lunch' ? 'selected' : ''}>Lunch</option>
                                    <option value="Dinner" ${meal.meal_type === 'Dinner' ? 'selected' : ''}>Dinner</option>
                                    <option value="Snack" ${meal.meal_type === 'Snack' ? 'selected' : ''}>Snack</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Restaurant</label>
                                <input type="text" class="form-control" name="restaurant" 
                                       value="${meal.restaurant || ''}" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Meal Time</label>
                                <input type="time" class="form-control" name="meal_time" 
                                       value="${meal.meal_time || ''}" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" name="location" 
                                       value="${meal.location || ''}" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="mb-3">
                                <label class="form-label">Cost per Person</label>
                                <input type="number" class="form-control" name="cost_per_person" 
                                       value="${meal.cost_per_person}" step="0.01" min="0" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="mb-3">
                                <label class="form-label">Total Cost</label>
                                <input type="number" class="form-control" name="total_cost" 
                                       value="${meal.total_cost}" step="0.01" min="0" ${meal.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="mb-3">
                                <label class="form-label">Currency</label>
                                <select class="form-select" name="currency" ${meal.is_locked ? 'disabled' : ''}>
                                    <option value="USD" ${meal.currency === 'USD' ? 'selected' : ''}>USD</option>
                                    <option value="EUR" ${meal.currency === 'EUR' ? 'selected' : ''}>EUR</option>
                                    <option value="JOD" ${meal.currency === 'JOD' ? 'selected' : ''}>JOD</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    ${!meal.is_locked ? `
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="servicesManager.deleteService('meal', ${meal.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                            <button type="submit" class="btn btn-primary btn-sm">
                                <i class="fas fa-save"></i> Save Meal
                            </button>
                        </div>
                    ` : ''}
                </form>
            </div>
        `;
        return card;
    }

    renderGuides() {
        const container = document.getElementById('guidesContainer');
        if (!container) return;

        container.innerHTML = '';
        
        this.services.guides.forEach((guide, index) => {
            const guideCard = this.createGuideCard(guide, index);
            container.appendChild(guideCard);
        });
    }

    createGuideCard(guide, index) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-user-tie text-success"></i>
                    ${guide.guide_name || 'Guide Service'} - ${guide.service_type || ''}
                </h6>
                <div>
                    ${guide.is_locked ? '<span class="badge bg-warning">Locked</span>' : ''}
                    <span class="badge bg-${this.getStatusBadgeClass(guide.status)}">${guide.status}</span>
                </div>
            </div>
            <div class="card-body">
                <form class="service-form" data-service-type="guide" data-service-id="${guide.id}">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Date</label>
                                <input type="date" class="form-control" name="date" 
                                       value="${guide.date}" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Guide Name</label>
                                <input type="text" class="form-control" name="guide_name" 
                                       value="${guide.guide_name || ''}" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Language</label>
                                <input type="text" class="form-control" name="language" 
                                       value="${guide.language || ''}" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Service Type</label>
                                <select class="form-select" name="service_type" ${guide.is_locked ? 'disabled' : ''}>
                                    <option value="Meet & Greet" ${guide.service_type === 'Meet & Greet' ? 'selected' : ''}>Meet & Greet</option>
                                    <option value="Tour Guide" ${guide.service_type === 'Tour Guide' ? 'selected' : ''}>Tour Guide</option>
                                    <option value="Transfer Guide" ${guide.service_type === 'Transfer Guide' ? 'selected' : ''}>Transfer Guide</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Duration (Hours)</label>
                                <input type="number" class="form-control" name="duration_hours" 
                                       value="${guide.duration_hours || ''}" step="0.5" min="0" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Meeting Time</label>
                                <input type="time" class="form-control" name="meeting_time" 
                                       value="${guide.meeting_time || ''}" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Cost</label>
                                <input type="number" class="form-control" name="cost" 
                                       value="${guide.cost}" step="0.01" min="0" ${guide.is_locked ? 'readonly' : ''}>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">Currency</label>
                                <select class="form-select" name="currency" ${guide.is_locked ? 'disabled' : ''}>
                                    <option value="USD" ${guide.currency === 'USD' ? 'selected' : ''}>USD</option>
                                    <option value="EUR" ${guide.currency === 'EUR' ? 'selected' : ''}>EUR</option>
                                    <option value="JOD" ${guide.currency === 'JOD' ? 'selected' : ''}>JOD</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Meeting Point</label>
                        <input type="text" class="form-control" name="meeting_point" 
                               value="${guide.meeting_point || ''}" ${guide.is_locked ? 'readonly' : ''}>
                    </div>
                    ${!guide.is_locked ? `
                        <div class="d-flex justify-content-between">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="servicesManager.deleteService('guide', ${guide.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                            <button type="submit" class="btn btn-primary btn-sm">
                                <i class="fas fa-save"></i> Save Guide
                            </button>
                        </div>
                    ` : ''}
                </form>
            </div>
        `;
        return card;
    }

    getStatusBadgeClass(status) {
        switch (status) {
            case 'REQUEST': return 'warning';
            case 'BOOKED': return 'info';
            case 'IN_PROGRESS': return 'primary';
            case 'CONFIRMED': return 'success';
            default: return 'secondary';
        }
    }

    async handleServiceFormSubmit(form) {
        const serviceType = form.dataset.serviceType;
        const serviceId = form.dataset.serviceId;
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch(`/inbound/api/${this.requestId}/services/${serviceType}/${serviceId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                this.showMessage(`${serviceType} updated successfully!`, 'success');
                await this.loadServices(); // Reload to get updated data
            } else {
                throw new Error(result.error || 'Update failed');
            }
        } catch (error) {
            console.error('Error updating service:', error);
            this.showMessage('Error updating service: ' + error.message, 'error');
        }
    }

    async deleteService(serviceType, serviceId) {
        if (!confirm(`Delete this ${serviceType} service?`)) {
            return;
        }

        try {
            const response = await fetch(`/inbound/api/${this.requestId}/services/${serviceType}/${serviceId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                this.showMessage(`${serviceType} deleted successfully!`, 'success');
                await this.loadServices(); // Reload to refresh display
            } else {
                throw new Error(result.error || 'Delete failed');
            }
        } catch (error) {
            console.error('Error deleting service:', error);
            this.showMessage('Error deleting service: ' + error.message, 'error');
        }
    }

    showMessage(message, type = 'info') {
        // Reuse the same toast functionality from itinerary.js
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Initialize and show the toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove the toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }
}

// Global variable to be used by inline event handlers
let servicesManager;