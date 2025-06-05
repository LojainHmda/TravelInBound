document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a booking form page
    const isBookingForm = document.getElementById('start_date') !== null;

    if (isBookingForm) {
        // Service selection enhancement
        const serviceOptions = document.querySelectorAll('.service-option');
        if (serviceOptions.length > 0) {
            serviceOptions.forEach(option => {
                option.addEventListener('click', function(e) {
                    const checkbox = this.querySelector('input[type="checkbox"]');
                    if (e.target !== checkbox) {
                        checkbox.checked = !checkbox.checked;
                    }
                });
            });
        }

        // Date range validation
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');

        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', validateDateRange);
            endDateInput.addEventListener('change', validateDateRange);

            // Set min date to today for start_date
            const today = new Date().toISOString().split('T')[0];
            if (startDateInput) {
                startDateInput.setAttribute('min', today);
            }
        }

        // Service type change handler
        const serviceTypeSelect = document.getElementById('service_type');
        if (serviceTypeSelect) {
            serviceTypeSelect.addEventListener('change', function() {
                updateDescriptionPlaceholder(this.value);
            });

            // Initialize with the current value
            updateDescriptionPlaceholder(serviceTypeSelect.value);
        }
    }

    // Tab functionality (applies to all pages)
    // Initialize tab functionality from URL hash if present
    if (window.location.hash) {
        const tabId = window.location.hash.substring(1);
        const tab = document.querySelector(`#${tabId}-tab`);
        if (tab) {
            try {
                const tabInstance = new bootstrap.Tab(tab);
                tabInstance.show();
            } catch (error) {
                console.log('Tab initialization error:', error);
            }
        }
    }

    // Update URL hash when tab is shown
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    if (tabEls.length > 0) {
        tabEls.forEach(tabEl => {
            tabEl.addEventListener('shown.bs.tab', function (e) {
                if (e.target && e.target.getAttribute) {
                    const id = e.target.getAttribute('aria-controls');
                    if (id) {
                        window.location.hash = id;
                    }
                }
            });
        });
    }

    // Delete functionality works through inline forms with JavaScript confirmation
    const deleteForms = document.querySelectorAll('form[action*="delete_service_item"]');
});

// Validate that end date is after start date
function validateDateRange() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);

        if (endDate < startDate) {
            alert('End date must be after start date');
            endDateInput.value = '';
        }

        // Set min date for end_date based on start_date
        if (startDateInput.value) {
            endDateInput.setAttribute('min', startDateInput.value);
        }
    }
}

// Update description placeholder based on service type
function updateDescriptionPlaceholder(serviceType) {
    const descriptionField = document.getElementById('description');
    if (!descriptionField) return;

    let placeholder = '';

    switch (serviceType) {
        case 'FLIGHT':
            placeholder = 'E.g., One-way flight from New York to London, Economy class';
            break;
        case 'HOTEL':
            placeholder = 'E.g., 5 nights at Grand Hotel, Double room with breakfast';
            break;
        case 'TRANSPORT':
            placeholder = 'E.g., Airport transfer from Heathrow to central London';
            break;
        case 'VISA':
            placeholder = 'E.g., Tourist visa application for United Kingdom';
            break;
        case 'INSURANCE':
            placeholder = 'E.g., Comprehensive travel insurance for 7 days';
            break;
        default:
            placeholder = 'Enter service description';
    }

    // Only set attribute if the element exists
    if (descriptionField) {
        descriptionField.setAttribute('placeholder', placeholder);
    }
}