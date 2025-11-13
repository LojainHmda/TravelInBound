/**
 * Itinerary Management Module for Inbound Tour Operator
 * Handles itinerary generation, cost calculations, and service flag management
 */

class ItineraryManager {
    constructor(requestId, paxCount) {
        this.requestId = requestId;
        this.paxCount = paxCount;
        this.itineraryData = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadItinerary();
    }

    bindEvents() {
        // Generator buttons
        document.getElementById('generateByDays')?.addEventListener('click', () => this.generateByDays());
        document.getElementById('generateBySections')?.addEventListener('click', () => this.generateBySections());
        
        // CRUD buttons
        document.getElementById('addRow')?.addEventListener('click', () => this.addRow());
        document.getElementById('saveItinerary')?.addEventListener('click', () => this.saveItinerary());
    }

    async loadItinerary() {
        try {
            const response = await fetch(`/inbound/api/${this.requestId}/itinerary`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.itineraryData = data.rows || [];
            this.renderItineraryTable();
            this.updatePricingSummary();
            this.updateServiceCounts();
        } catch (error) {
            console.error('Error loading itinerary:', error);
            this.showMessage('Error loading itinerary: ' + error.message, 'error');
        }
    }

    renderItineraryTable() {
        const tbody = document.getElementById('itineraryBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        this.itineraryData.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = this.createRowHTML(row, index);
            tbody.appendChild(tr);
        });
    }

    createRowHTML(row, index) {
        return `
            <td>
                <input type="date" class="form-control form-control-sm" 
                       value="${row.date}" onchange="itineraryManager.updateRow(${index}, 'date', this.value)">
            </td>
            <td>
                <textarea class="form-control form-control-sm description-input" 
                          onchange="itineraryManager.updateRow(${index}, 'description', this.value)">${row.description}</textarea>
            </td>
            <td>
                <input type="number" class="form-control form-control-sm cost-input" 
                       value="${row.base_cost || 0}" step="0.01" min="0"
                       onchange="itineraryManager.updateRow(${index}, 'base_cost', parseFloat(this.value) || 0)">
            </td>
            <td>
                <select class="form-select form-select-sm" onchange="itineraryManager.updateRow(${index}, 'cost_unit', this.value)">
                    <option value="PER_PERSON" ${row.cost_unit === 'PER_PERSON' ? 'selected' : ''}>Per Person</option>
                    <option value="PER_GROUP" ${row.cost_unit === 'PER_GROUP' ? 'selected' : ''}>Per Group</option>
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm" onchange="itineraryManager.updateRow(${index}, 'currency', this.value)">
                    <option value="USD" ${row.currency === 'USD' ? 'selected' : ''}>USD</option>
                    <option value="EUR" ${row.currency === 'EUR' ? 'selected' : ''}>EUR</option>
                    <option value="JOD" ${row.currency === 'JOD' ? 'selected' : ''}>JOD</option>
                </select>
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input service-flag" 
                       ${row.flag_hotel ? 'checked' : ''} 
                       onchange="itineraryManager.updateRow(${index}, 'flag_hotel', this.checked)">
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input service-flag" 
                       ${row.flag_guide ? 'checked' : ''} 
                       onchange="itineraryManager.updateRow(${index}, 'flag_guide', this.checked)">
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input service-flag" 
                       ${row.flag_transport ? 'checked' : ''} 
                       onchange="itineraryManager.updateRow(${index}, 'flag_transport', this.checked)">
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input service-flag" 
                       ${row.flag_meal ? 'checked' : ''} 
                       onchange="itineraryManager.updateRow(${index}, 'flag_meal', this.checked)">
            </td>
            <td class="text-center">
                <input type="checkbox" class="form-check-input service-flag" 
                       ${row.flag_airport ? 'checked' : ''} 
                       onchange="itineraryManager.updateRow(${index}, 'flag_airport', this.checked)">
            </td>
            <td class="fw-bold row-cost">${(row.row_cost || 0).toFixed(2)} ${row.currency}</td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="itineraryManager.removeRow(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
    }

    updateRow(index, field, value) {
        if (index >= this.itineraryData.length) return;
        
        this.itineraryData[index][field] = value;
        
        // Recalculate row cost
        this.calculateRowCost(index);
        
        // Update the display
        this.updateRowCostDisplay(index);
        this.updatePricingSummary();
        this.updateServiceCounts();
    }

    calculateRowCost(index) {
        const row = this.itineraryData[index];
        if (row.cost_unit === 'PER_PERSON') {
            row.row_cost = (row.base_cost || 0) * this.paxCount;
        } else {
            row.row_cost = row.base_cost || 0;
        }
    }

    updateRowCostDisplay(index) {
        const tbody = document.getElementById('itineraryBody');
        if (!tbody || !tbody.children[index]) return;
        
        const row = this.itineraryData[index];
        const rowElement = tbody.children[index];
        const costCell = rowElement.querySelector('.row-cost');
        
        if (costCell) {
            costCell.textContent = `${(row.row_cost || 0).toFixed(2)} ${row.currency}`;
        }
    }

    addRow() {
        const newRow = {
            id: null,
            date: new Date().toISOString().split('T')[0],
            description: '',
            base_cost: 0,
            cost_unit: 'PER_PERSON',
            currency: 'USD',
            flag_hotel: false,
            flag_guide: false,
            flag_transport: false,
            flag_meal: false,
            flag_airport: false,
            row_cost: 0
        };
        
        this.itineraryData.push(newRow);
        this.renderItineraryTable();
        this.updatePricingSummary();
        this.updateServiceCounts();
    }

    removeRow(index) {
        if (confirm('Remove this itinerary row?')) {
            this.itineraryData.splice(index, 1);
            this.renderItineraryTable();
            this.updatePricingSummary();
            this.updateServiceCounts();
        }
    }

    async generateByDays() {
        if (!confirm('This will replace all existing itinerary rows. Continue?')) {
            return;
        }

        try {
            const response = await fetch(`/inbound/api/${this.requestId}/generate-days`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            const result = await response.json();
            if (result.success) {
                await this.loadItinerary();
                this.showMessage('Itinerary generated by days successfully!', 'success');
            } else {
                throw new Error(result.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Error generating by days:', error);
            this.showMessage('Error generating itinerary: ' + error.message, 'error');
        }
    }

    async generateBySections() {
        if (!confirm('This will replace all existing itinerary rows. Continue?')) {
            return;
        }

        try {
            const response = await fetch(`/inbound/api/${this.requestId}/generate-sections`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            const result = await response.json();
            if (result.success) {
                await this.loadItinerary();
                this.showMessage('Itinerary generated by sections successfully!', 'success');
            } else {
                throw new Error(result.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Error generating by sections:', error);
            this.showMessage('Error generating itinerary: ' + error.message, 'error');
        }
    }

    async saveItinerary() {
        try {
            // Collect arrival/departure data from the form
            const arrival_point = document.getElementById('itinerary_arrival_point')?.value || '';
            const arrival_time = document.getElementById('itinerary_arrival_time')?.value || '';
            const departure_point = document.getElementById('itinerary_departure_point')?.value || '';
            const departure_time = document.getElementById('itinerary_departure_time')?.value || '';
            
            const response = await fetch(`/inbound/api/${this.requestId}/itinerary`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    rows: this.itineraryData,
                    arrival_point: arrival_point,
                    arrival_time: arrival_time,
                    departure_point: departure_point,
                    departure_time: departure_time
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showMessage('Itinerary saved successfully!', 'success');
                await this.loadItinerary(); // Reload to get updated IDs and service counts
            } else {
                throw new Error(result.error || 'Save failed');
            }
        } catch (error) {
            console.error('Error saving itinerary:', error);
            this.showMessage('Error saving itinerary: ' + error.message, 'error');
        }
    }

    updatePricingSummary() {
        // Group by date for daily totals
        const dailyTotals = {};
        let grandTotal = 0;
        
        this.itineraryData.forEach(row => {
            const dateKey = row.date;
            if (!dailyTotals[dateKey]) {
                dailyTotals[dateKey] = 0;
            }
            dailyTotals[dateKey] += row.row_cost || 0;
            grandTotal += row.row_cost || 0;
        });
        
        // Render daily totals
        const summaryDiv = document.getElementById('pricingSummary');
        if (!summaryDiv) return;
        
        let summaryHTML = '';
        
        Object.keys(dailyTotals).sort().forEach(date => {
            const total = dailyTotals[date];
            const dateObj = new Date(date);
            const formattedDate = dateObj.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric'
            });
            
            summaryHTML += `
                <div class="d-flex justify-content-between daily-total">
                    <span>${formattedDate}</span>
                    <span>${total.toFixed(2)} USD</span>
                </div>
            `;
        });
        
        summaryDiv.innerHTML = summaryHTML || '<div class="text-muted">No items</div>';
        
        // Update grand total
        const grandTotalElement = document.getElementById('grandTotal');
        if (grandTotalElement) {
            grandTotalElement.textContent = `${grandTotal.toFixed(2)} USD`;
        }
    }

    updateServiceCounts() {
        const counts = {
            hotel: 0,
            transport: 0,
            meal: 0,
            guide: 0,
            airport: 0
        };
        
        this.itineraryData.forEach(row => {
            if (row.flag_hotel) counts.hotel++;
            if (row.flag_transport) counts.transport++;
            if (row.flag_meal) counts.meal++;
            if (row.flag_guide) counts.guide++;
            if (row.flag_airport) counts.airport++;
        });
        
        // Update count displays
        const elements = {
            hotelCount: counts.hotel,
            transportCount: counts.transport,
            mealCount: counts.meal,
            guideCount: counts.guide,
            airportCount: counts.airport
        };
        
        Object.keys(elements).forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = elements[elementId];
            }
        });
    }

    showMessage(message, type = 'info') {
        // Create a toast-style message
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
let itineraryManager;