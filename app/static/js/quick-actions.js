/**
 * Quick Actions Floating Button JavaScript
 * Provides instant access to common travel booking actions
 */

class QuickActionsFAB {
    constructor() {
        this.isOpen = false;
        this.fab = null;
        this.actions = null;
        this.init();
    }

    init() {
        this.createFAB();
        this.bindEvents();
    }

    createFAB() {
        // Create the floating action button container
        const fabContainer = document.createElement('div');
        fabContainer.className = 'quick-actions-fab';
        fabContainer.innerHTML = `
            <div class="fab-actions" id="fabActions">
                <a href="/booking/new" class="fab-action" data-tooltip="New Booking">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                    </svg>
                    <span class="fab-text">New Booking</span>
                </a>
                
                <a href="/customer/new" class="fab-action" data-tooltip="Add Customer">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    <span class="fab-text">Add Customer</span>
                </a>
                
                <a href="/finance" class="fab-action" data-tooltip="Finance Dashboard">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                    </svg>
                    <span class="fab-text">Finance</span>
                </a>
                
                <a href="/supplier" class="fab-action" data-tooltip="Suppliers">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                    </svg>
                    <span class="fab-text">Suppliers</span>
                </a>
                
                <button class="fab-action" onclick="quickActions.showQuickSearch()" data-tooltip="Quick Search">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <span class="fab-text">Search</span>
                </button>
                
                <button class="fab-action" onclick="quickActions.hideFAB()" data-tooltip="Hide Quick Actions">
                    <svg class="fab-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"/>
                    </svg>
                    <span class="fab-text">Hide</span>
                </button>
            </div>
            
            <button class="fab-main" id="fabMain">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
            </button>
        `;

        document.body.appendChild(fabContainer);
        
        this.fab = document.getElementById('fabMain');
        this.actions = document.getElementById('fabActions');
    }

    bindEvents() {
        // Toggle FAB on click
        this.fab.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggle();
        });

        // Close FAB when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.quick-actions-fab') && this.isOpen) {
                this.close();
            }
        });

        // Close FAB on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Add click tracking for analytics
        this.actions.addEventListener('click', (e) => {
            if (e.target.closest('.fab-action')) {
                const action = e.target.closest('.fab-action');
                const actionName = action.querySelector('.fab-text')?.textContent || 'Unknown';
                console.log(`Quick Action clicked: ${actionName}`);
                
                // Close FAB after action click
                setTimeout(() => this.close(), 100);
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        this.fab.classList.add('active');
        this.actions.classList.add('show');
        
        // Animate actions with stagger
        const actionItems = this.actions.querySelectorAll('.fab-action');
        actionItems.forEach((item, index) => {
            setTimeout(() => {
                item.style.transform = 'scale(1) translateX(0)';
                item.style.opacity = '1';
            }, index * 50);
        });
    }

    close() {
        this.isOpen = false;
        this.fab.classList.remove('active');
        this.actions.classList.remove('show');
        
        // Reset action animations
        const actionItems = this.actions.querySelectorAll('.fab-action');
        actionItems.forEach(item => {
            item.style.transform = '';
            item.style.opacity = '';
        });
    }

    showQuickSearch() {
        // Create quick search modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Quick Search</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control mb-3" id="quickSearchInput" placeholder="Search bookings, customers, or reference numbers...">
                        <div id="quickSearchResults" class="list-group">
                            <div class="text-muted text-center py-3">Start typing to search...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize Bootstrap modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Focus search input
        modal.addEventListener('shown.bs.modal', () => {
            document.getElementById('quickSearchInput').focus();
        });
        
        // Clean up modal after hide
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
        
        // Add search functionality
        this.setupQuickSearch();
        this.close();
    }

    setupQuickSearch() {
        const searchInput = document.getElementById('quickSearchInput');
        const resultsContainer = document.getElementById('quickSearchResults');
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                resultsContainer.innerHTML = '<div class="text-muted text-center py-3">Start typing to search...</div>';
                return;
            }

            searchTimeout = setTimeout(() => {
                this.performQuickSearch(query, resultsContainer);
            }, 300);
        });
    }

    async performQuickSearch(query, container) {
        try {
            container.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div> Searching...</div>';
            
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error('Search failed');
            }
            
            const results = await response.json();
            this.displaySearchResults(results, container);
            
        } catch (error) {
            container.innerHTML = '<div class="text-danger text-center py-3">Search failed. Please try again.</div>';
        }
    }

    displaySearchResults(results, container) {
        if (!results || (results.bookings?.length === 0 && results.customers?.length === 0)) {
            container.innerHTML = '<div class="text-muted text-center py-3">No results found.</div>';
            return;
        }

        let html = '';
        
        if (results.bookings?.length > 0) {
            html += '<h6 class="text-muted mb-2">Bookings</h6>';
            results.bookings.forEach(booking => {
                html += `
                    <a href="/booking/${booking.id}" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${booking.reference_number}</h6>
                            <small class="text-muted">${booking.status}</small>
                        </div>
                        <p class="mb-1">${booking.customer_name || 'Unknown Customer'}</p>
                        <small class="text-muted">Total: $${booking.total_amount || '0.00'}</small>
                    </a>
                `;
            });
        }
        
        if (results.customers?.length > 0) {
            html += '<h6 class="text-muted mb-2 mt-3">Customers</h6>';
            results.customers.forEach(customer => {
                html += `
                    <a href="/customer/${customer.id}" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${customer.name}</h6>
                        </div>
                        <p class="mb-1">${customer.email || ''}</p>
                        <small class="text-muted">${customer.phone || ''}</small>
                    </a>
                `;
            });
        }
        
        container.innerHTML = html;
    }

    hideFAB() {
        // Hide the entire FAB container
        const fabContainer = document.querySelector('.quick-actions-fab');
        if (fabContainer) {
            fabContainer.style.display = 'none';
            
            // Save state to localStorage
            localStorage.setItem('quickActionsFabHidden', 'true');
            
            // Create a small show button
            this.createShowButton();
        }
    }

    showFAB() {
        // Show the FAB container
        const fabContainer = document.querySelector('.quick-actions-fab');
        if (fabContainer) {
            fabContainer.style.display = 'block';
            
            // Remove state from localStorage
            localStorage.setItem('quickActionsFabHidden', 'false');
            
            // Remove show button
            const showButton = document.getElementById('showFabButton');
            if (showButton) {
                showButton.remove();
            }
        }
    }

    createShowButton() {
        // Don't create if already exists
        if (document.getElementById('showFabButton')) return;
        
        const showButton = document.createElement('button');
        showButton.id = 'showFabButton';
        showButton.className = 'show-fab-button';
        showButton.innerHTML = `
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
        `;
        showButton.title = 'Show Quick Actions';
        showButton.onclick = () => this.showFAB();
        
        document.body.appendChild(showButton);
    }

    // Check if FAB should be hidden on initialization
    checkInitialState() {
        if (localStorage.getItem('quickActionsFabHidden') === 'true') {
            setTimeout(() => this.hideFAB(), 100);
        }
    }
}

// Initialize Quick Actions FAB when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quickActions = new QuickActionsFAB();
    // Check if it should be hidden initially
    window.quickActions.checkInitialState();
});