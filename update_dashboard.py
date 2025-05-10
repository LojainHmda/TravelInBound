#!/usr/bin/env python3

# Script to update the dashboard.html template with the View button for all service types

dashboard_file = 'app/templates/dashboard.html'

# Read the original file
with open(dashboard_file, 'r') as file:
    content = file.read()

# Replace the buttons section for each service type
old_button_section = '''                                        <div class="btn-group">
                                            {% if item.status == 'REQUEST' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-primary">
                                                    <i class="fas fa-check me-1"></i>Confirm
                                                </a>
                                            {% elif item.status == 'IN_PROGRESS' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye me-1"></i>View
                                                </a>
                                            {% endif %}'''

new_button_section = '''                                        <div class="btn-group">
                                            {% set conf_doc = item.documents|selectattr('document_type', 'equalto', 'CONFIRMATION')|first %}
                                            {% if conf_doc %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye me-1"></i>View
                                                </a>
                                            {% elif item.status == 'REQUEST' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-primary">
                                                    <i class="fas fa-check me-1"></i>Confirm
                                                </a>
                                            {% elif item.status == 'IN_PROGRESS' or item.status == 'CONFIRMED' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye me-1"></i>View
                                                </a>
                                            {% endif %}'''

updated_content = content.replace(old_button_section, new_button_section)

# Write the updated content back to the file
with open(dashboard_file, 'w') as file:
    file.write(updated_content)

print(f"Successfully updated {dashboard_file}")