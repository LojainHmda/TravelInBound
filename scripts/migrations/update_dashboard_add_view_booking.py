#!/usr/bin/env python3

# Script to add the View Booking button to all service type tables in dashboard.html

dashboard_file = 'app/templates/dashboard.html'

# Read the original file
with open(dashboard_file, 'r') as file:
    content = file.read()

# Replace the button group closing in each service type tab
old_pattern = '''                                            {% endif %}
                                        </div>'''

new_pattern = '''                                            {% endif %}
                                            <button class="btn btn-sm btn-dark-blue view-booking-btn" style="background-color: var(--dark-blue); color: white;" data-booking-id="{{ item.booking_id }}">
                                                <i class="fas fa-info-circle"></i>
                                            </button>
                                        </div>'''

updated_content = content.replace(old_pattern, new_pattern)

# Write the updated content back to the file
with open(dashboard_file, 'w') as file:
    file.write(updated_content)

print(f"Successfully updated {dashboard_file} with View Booking buttons")