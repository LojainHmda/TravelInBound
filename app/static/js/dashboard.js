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
}

// Setup view buttons to show details inline
function setupViewButtons() {
    const viewButtons = document.querySelectorAll('.view-booking-btn');
    
    viewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const bookingId = this.getAttribute('data-booking-id');
            const detailsRow = document.getElementById(`booking-details-${bookingId}`);
            
            // Toggle details visibility
            if (detailsRow) {
                if (detailsRow.classList.contains('d-none')) {
                    // Hide any other open details first
                    document.querySelectorAll('.booking-details-row').forEach(row => {
                        row.classList.add('d-none');
                    });
                    
                    // Show this one
                    detailsRow.classList.remove('d-none');
                    this.innerHTML = '<i class="fas fa-chevron-up"></i> Hide';
                } else {
                    detailsRow.classList.add('d-none');
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
            const colCount = parentRow.querySelectorAll('td').length;
            
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
        })
        .catch(error => {
            console.error('Error loading booking details:', error);
            button.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error';
        });
}

// Create HTML for booking details
function createDetailsHTML(booking) {
    // This is a placeholder - the actual API would return structured data
    let html = `
    <div class="booking-details-container p-3">
        <h5 class="border-bottom pb-2">Booking Reference: ${booking.reference_number}</h5>
        
        <div class="row">
            <div class="col-md-8">
                <!-- Service Items -->
                <div class="card mb-3">
                    <div class="card-header bg-dark-blue text-white py-2">
                        <h6 class="mb-0"><i class="fas fa-list me-2"></i>Service Items</h6>
                    </div>
                    <div class="card-body p-0">
                        <table class="table mb-0">
                            <thead>
                                <tr>
                                    <th>Service</th>
                                    <th>Dates</th>
                                    <th>Description</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>`;
    
    // Add service items
    if (booking.service_items && booking.service_items.length > 0) {
        booking.service_items.forEach(item => {
            html += `
                <tr>
                    <td>${item.service_type}</td>
                    <td>${item.start_date} - ${item.end_date}</td>
                    <td>${item.description}</td>
                    <td>$${item.amount.toFixed(2)}</td>
                    <td><span class="badge bg-orange" style="display: inline-block; min-width: 80px; text-align: center;">${item.status}</span></td>
                </tr>`;
        });
    } else {
        html += `<tr><td colspan="5" class="text-center">No service items found</td></tr>`;
    }
    
    html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- Customer Info -->
                <div class="card mb-3">
                    <div class="card-header bg-dark-blue text-white py-2">
                        <h6 class="mb-0"><i class="fas fa-user me-2"></i>Customer</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-1"><strong>Name:</strong> ${booking.customer_name}</p>
                        <p class="mb-1"><strong>Email:</strong> ${booking.customer_email}</p>
                        <p class="mb-0"><strong>Total:</strong> $${booking.total_amount.toFixed(2)}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-end mt-2">
            <a href="/booking/${booking.id}/details" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-external-link-alt me-1"></i> Full Details
            </a>
        </div>
    </div>`;
    
    return html;
}