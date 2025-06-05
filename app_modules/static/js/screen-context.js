/**
 * Screen Context Capture for AI Chat
 * Reads current screen state and enables contextual AI actions
 */

class ScreenContextCapture {
    constructor() {
        this.currentContext = {};
        this.init();
    }

    init() {
        // Capture context on page changes
        this.captureCurrentContext();
        
        // Update context when DOM changes
        this.observeChanges();
    }

    captureCurrentContext() {
        this.currentContext = {
            page: this.getPageType(),
            url: window.location.href,
            pathname: window.location.pathname,
            title: document.title,
            visible_data: this.extractVisibleData(),
            form_fields: this.getFormFields(),
            table_data: this.getTableData(),
            selected_items: this.getSelectedItems(),
            available_actions: this.getAvailableActions(),
            current_data: this.getCurrentPageData(),
            timestamp: new Date().toISOString()
        };

        return this.currentContext;
    }

    getPageType() {
        const path = window.location.pathname;
        
        if (path.includes('/booking/') && path.match(/\/booking\/\d+/)) {
            return 'booking_details';
        } else if (path.includes('/booking')) {
            return 'booking_list';
        } else if (path.includes('/customer/') && path.match(/\/customer\/\d+/)) {
            return 'customer_details';
        } else if (path.includes('/customer')) {
            return 'customer_list';
        } else if (path.includes('/finance')) {
            return 'finance_dashboard';
        } else if (path.includes('/dashboard')) {
            return 'main_dashboard';
        } else if (path === '/') {
            return 'home';
        }
        
        return 'unknown';
    }

    extractVisibleData() {
        const visibleData = {};

        // Extract data from cards
        const cards = document.querySelectorAll('.card, .booking-card, .metric-card');
        cards.forEach((card, index) => {
            const cardData = this.extractCardData(card);
            if (cardData) {
                visibleData[`card_${index}`] = cardData;
            }
        });

        // Extract key metrics
        const metrics = document.querySelectorAll('[class*="metric"], [class*="stat"], .badge');
        metrics.forEach((metric, index) => {
            const text = metric.textContent?.trim();
            if (text && text.length > 0 && text.length < 100) {
                visibleData[`metric_${index}`] = text;
            }
        });

        return visibleData;
    }

    extractCardData(card) {
        const data = {};
        
        // Extract booking reference
        const refElement = card.querySelector('[data-booking-ref], .reference-number');
        if (refElement) {
            data.booking_reference = refElement.textContent?.trim();
        }

        // Extract customer info
        const customerElement = card.querySelector('[data-customer], .customer-name');
        if (customerElement) {
            data.customer_name = customerElement.textContent?.trim();
        }

        // Extract amounts
        const amountElement = card.querySelector('[data-amount], .amount, [class*="price"]');
        if (amountElement) {
            data.amount = amountElement.textContent?.trim();
        }

        // Extract status
        const statusElement = card.querySelector('[data-status], .status, .badge');
        if (statusElement) {
            data.status = statusElement.textContent?.trim();
        }

        // Extract IDs from data attributes or URLs
        const idElement = card.querySelector('[data-id]') || card;
        if (idElement.dataset.id) {
            data.id = idElement.dataset.id;
        }

        // Extract from onclick handlers
        const onclick = card.getAttribute('onclick');
        if (onclick) {
            const idMatch = onclick.match(/\/(\d+)/);
            if (idMatch) {
                data.id = idMatch[1];
            }
        }

        return Object.keys(data).length > 0 ? data : null;
    }

    getFormFields() {
        const forms = document.querySelectorAll('form');
        const formData = {};

        forms.forEach((form, formIndex) => {
            const fields = {};
            
            // Get all input fields
            form.querySelectorAll('input, select, textarea').forEach(field => {
                if (field.name && field.type !== 'password') {
                    fields[field.name] = {
                        type: field.type,
                        value: field.value,
                        required: field.required,
                        readonly: field.readOnly
                    };
                }
            });

            if (Object.keys(fields).length > 0) {
                formData[`form_${formIndex}`] = fields;
            }
        });

        return formData;
    }

    getTableData() {
        const tables = document.querySelectorAll('table');
        const tableData = {};

        tables.forEach((table, tableIndex) => {
            const rows = [];
            const headers = [];

            // Get headers
            const headerRow = table.querySelector('thead tr, tr:first-child');
            if (headerRow) {
                headerRow.querySelectorAll('th, td').forEach(cell => {
                    headers.push(cell.textContent?.trim() || '');
                });
            }

            // Get data rows (limit to first 10 for performance)
            const dataRows = table.querySelectorAll('tbody tr, tr:not(:first-child)');
            Array.from(dataRows).slice(0, 10).forEach(row => {
                const rowData = {};
                row.querySelectorAll('td, th').forEach((cell, cellIndex) => {
                    const header = headers[cellIndex] || `col_${cellIndex}`;
                    rowData[header] = cell.textContent?.trim() || '';
                });
                
                // Extract row ID if available
                if (row.dataset.id) {
                    rowData.row_id = row.dataset.id;
                }

                rows.push(rowData);
            });

            if (rows.length > 0) {
                tableData[`table_${tableIndex}`] = {
                    headers: headers,
                    rows: rows
                };
            }
        });

        return tableData;
    }

    getSelectedItems() {
        const selected = [];
        
        // Check for checked checkboxes
        document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
            if (checkbox.value && checkbox.value !== 'on') {
                selected.push({
                    type: 'checkbox',
                    value: checkbox.value,
                    id: checkbox.id || checkbox.name
                });
            }
        });

        // Check for selected table rows
        document.querySelectorAll('tr.selected, .selected').forEach(element => {
            const id = element.dataset.id || element.id;
            if (id) {
                selected.push({
                    type: 'row',
                    id: id
                });
            }
        });

        return selected;
    }

    getAvailableActions() {
        const actions = [];

        // Find buttons and links
        document.querySelectorAll('button, .btn, a[href]').forEach(element => {
            const text = element.textContent?.trim();
            const href = element.getAttribute('href');
            const onclick = element.getAttribute('onclick');
            
            if (text && text.length > 0 && text.length < 50) {
                actions.push({
                    text: text,
                    href: href,
                    type: element.tagName.toLowerCase(),
                    has_action: !!(href || onclick)
                });
            }
        });

        return actions.slice(0, 20); // Limit for performance
    }

    getCurrentPageData() {
        const pageData = {};
        
        // Extract page-specific data based on page type
        const pageType = this.getPageType();
        
        if (pageType === 'booking_details') {
            // Extract booking ID from URL
            const match = window.location.pathname.match(/\/booking\/(\d+)/);
            if (match) {
                pageData.booking_id = match[1];
            }
            
            // Extract booking reference from page
            const refElement = document.querySelector('[data-booking-ref], .reference-number, h1, h2');
            if (refElement) {
                const refMatch = refElement.textContent?.match(/IR-[A-Za-z0-9]+/);
                if (refMatch) {
                    pageData.booking_reference = refMatch[0];
                }
            }
        }
        
        if (pageType === 'customer_details') {
            // Extract customer ID from URL
            const match = window.location.pathname.match(/\/customer\/(\d+)/);
            if (match) {
                pageData.customer_id = match[1];
            }
        }

        return pageData;
    }

    observeChanges() {
        // Update context when DOM changes
        const observer = new MutationObserver(() => {
            // Debounce context updates
            clearTimeout(this.updateTimeout);
            this.updateTimeout = setTimeout(() => {
                this.captureCurrentContext();
            }, 500);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-id', 'data-booking-ref', 'data-customer']
        });
    }

    getContextForAI() {
        return this.captureCurrentContext();
    }
}

// Global instance
window.screenContext = new ScreenContextCapture();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.screenContext.init();
});