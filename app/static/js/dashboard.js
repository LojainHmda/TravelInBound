// Dashboard JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const hash = window.location.hash;
    if (hash) {
        const tab = document.querySelector(hash);
        if (tab) {
            const triggerEl = document.querySelector(`button[data-bs-target="${hash}"]`);
            if (triggerEl) {
                new bootstrap.Tab(triggerEl).show();
            }
        }
    }

    // Set up view buttons for inline details
    setupViewButtons();
    
    // Tab click event handlers
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function (e) {
            // Clear any open details when switching tabs
            document.querySelectorAll('.booking-details-row').forEach(row => {
                row.remove();
            });
            
            // Reset all view buttons
            document.querySelectorAll('.view-booking-btn').forEach(btn => {
                btn.innerHTML = '<i class="fas fa-eye"></i> View';
            });
        });
    });
});

// Filter bookings by status
function filterBookings(status) {
    const bookingTable = document.getElementById('bookingTable');
    const rows = bookingTable.querySelectorAll('tbody tr');
    const title = document.getElementById('bookingTableTitle');
    
    if (status === '') {
        // Show all
        rows.forEach(row => row.style.display = '');
        title.innerHTML = '<i class="fas fa-list-alt me-2"></i>All Booking Requests';
        document.getElementById('resetFilterBtn').style.display = 'none';
    } else {
        // Filter by status
        rows.forEach(row => {
            const statusCell = row.querySelector('td:nth-child(3) .badge');
            if (statusCell && statusCell.textContent.trim() === status) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        title.innerHTML = `<i class="fas fa-filter me-2"></i>${status} Bookings`;
        document.getElementById('resetFilterBtn').style.display = 'inline-block';
    }
    
    // Clear any open details when filtering
    document.querySelectorAll('.booking-details-row').forEach(row => {
        row.remove();
    });
    
    // Reset all view buttons
    document.querySelectorAll('.view-booking-btn').forEach(btn => {
        btn.innerHTML = '<i class="fas fa-eye"></i> View';
    });
}

// Setup view buttons to show details inline
function setupViewButtons() {
    const viewButtons = document.querySelectorAll('.view-booking-btn');
    
    viewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const bookingId = this.getAttribute('data-booking-id');
            const detailsRow = document.getElementById(`booking-details-${bookingId}`);
            
            // Close any other open details first
            document.querySelectorAll('.booking-details-row').forEach(row => {
                if (row.id !== `booking-details-${bookingId}`) {
                    row.remove();
                }
            });
            
            // Reset all other view buttons
            document.querySelectorAll('.view-booking-btn').forEach(btn => {
                if (btn !== this) {
                    btn.innerHTML = '<i class="fas fa-eye"></i> View';
                }
            });
            
            // Toggle details visibility
            if (detailsRow) {
                if (detailsRow.classList.contains('d-none')) {
                    detailsRow.classList.remove('d-none');
                    this.innerHTML = '<i class="fas fa-chevron-up"></i> Hide';
                } else {
                    detailsRow.remove();
                    this.innerHTML = '<i class="fas fa-eye"></i> View';
                }
            } else {
                // Load details via AJAX if not already loaded
                loadBookingDetails(bookingId, this);
            }
        });
    });
}

// Load booking details via AJAX
function loadBookingDetails(bookingId, button) {
    // Show loading indicator
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    
    fetch(`/api/booking/${bookingId}/details`)
        .then(response => response.json())
        .then(data => {
            // Create details row
            const parentRow = button.closest('tr');
            const colCount = parentRow.cells.length;
            
            const detailsRow = document.createElement('tr');
            detailsRow.id = `booking-details-${bookingId}`;
            detailsRow.className = 'booking-details-row';
            
            const detailsCell = document.createElement('td');
            detailsCell.colSpan = colCount;
            detailsCell.innerHTML = createDetailsHTML(data);
            
            detailsRow.appendChild(detailsCell);
            
            // Insert after the parent row
            parentRow.parentNode.insertBefore(detailsRow, parentRow.nextSibling);
            
            // Update button
            button.innerHTML = '<i class="fas fa-chevron-up"></i> Hide';
            
            // Initialize confirm buttons in the details view
            initializeConfirmButtons();
        })
        .catch(error => {
            console.error('Error loading booking details:', error);
            button.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error';
            alert('Failed to load booking details. Please try again.');
        });
}

// Create HTML for booking details
function createDetailsHTML(booking) {
    // Get service item icon based on type
    function getServiceIcon(type) {
        const icons = {
            'FLIGHT': 'fa-plane',
            'HOTEL': 'fa-hotel',
            'TRANSPORT': 'fa-taxi',
            'VISA': 'fa-passport',
            'INSURANCE': 'fa-shield-alt'
        };
        return icons[type] || 'fa-briefcase';
    }
    
    let html = `
    <div class="booking-details-container">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">Booking Reference: ${booking.reference_number}</h5>
            <span class="badge bg-orange">${booking.status}</span>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <!-- Service Items -->
                <div class="card mb-3 shadow-sm">
                    <div class="card-header bg-dark-blue text-white py-2">
                        <h6 class="mb-0"><i class="fas fa-list me-2"></i>Service Items</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table mb-0">
                            <thead>
                                <tr class="table-light">
                                    <th>Service</th>
                                    <th>Dates</th>
                                    <th>Description</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>`;
    
    // Add service items
    if (booking.service_items && booking.service_items.length > 0) {
        booking.service_items.forEach(item => {
            let actionsHtml = '';
            
            // Display different actions based on status
            if (item.status === 'REQUEST') {
                actionsHtml = `
                    <a href="/booking/service/${item.id}/confirm" class="btn btn-sm btn-success me-1">
                        <i class="fas fa-check me-1"></i>Confirm
                    </a>`;
            } else if (item.status === 'IN_PROGRESS') {
                actionsHtml = `
                    <a href="/booking/service/${item.id}/confirm" class="btn btn-sm btn-primary me-1">
                        <i class="fas fa-edit me-1"></i>Edit
                    </a>`;
            }
            
            html += `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <i class="fas ${getServiceIcon(item.service_type)} service-icon-table me-2"></i>
                            ${item.service_type}
                        </div>
                    </td>
                    <td>${item.start_date} - ${item.end_date}</td>
                    <td>${item.description}</td>
                    <td>$${parseFloat(item.amount).toFixed(2)}</td>
                    <td><span class="badge bg-orange" style="display: inline-block; min-width: 80px; text-align: center;">${item.status}</span></td>
                    <td>${actionsHtml}</td>
                </tr>`;
        });
    } else {
        html += `<tr><td colspan="5" class="text-center py-3">No service items found</td></tr>`;
    }
    
    html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- Customer Info -->
                <div class="card mb-3 shadow-sm">
                    <div class="card-header bg-dark-blue text-white py-2">
                        <h6 class="mb-0"><i class="fas fa-user me-2"></i>Customer</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-1"><strong>Name:</strong> ${booking.customer_name}</p>
                        <p class="mb-1"><strong>Email:</strong> ${booking.customer_email}</p>
                        <p class="mb-0"><strong>Total:</strong> $${parseFloat(booking.total_amount).toFixed(2)}</p>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="card shadow-sm">
                    <div class="card-header bg-light py-2">
                        <h6 class="mb-0">Actions</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/booking/${booking.id}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-external-link-alt me-1"></i> Full Details
                            </a>
                            <button class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-print me-1"></i> Print Summary
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
    
    return html;
}