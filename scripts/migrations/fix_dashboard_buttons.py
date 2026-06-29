"""
Fix all dashboard confirm button logic to match the correct workflow
"""

def fix_dashboard_buttons():
    with open('app/templates/dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix all IN_PROGRESS sections to show Confirm button instead of View
    old_pattern = '''{% elif item.status == 'IN_PROGRESS' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye me-1"></i>View
                                                </a>'''
    
    new_pattern = '''{% elif item.status == 'IN_PROGRESS' %}
                                                <a href="{{ url_for('booking.confirm_service', item_id=item.id) }}" class="btn btn-sm btn-success">
                                                    <i class="fas fa-check me-1"></i>Confirm
                                                </a>'''
    
    content = content.replace(old_pattern, new_pattern)
    
    with open('app/templates/dashboard.html', 'w') as f:
        f.write(content)
    
    print("Dashboard button logic fixed successfully!")

if __name__ == "__main__":
    fix_dashboard_buttons()