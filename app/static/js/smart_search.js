class SmartSearch {
    constructor() {
        this.searchData = {
            agents: [],
            requestNumbers: [],
            nationalities: []
        };
        this.init();
    }

    init() {
        this.loadSearchData();
        this.setupAutocomplete();
    }

    async loadSearchData() {
        try {
            // Load existing data from the page or make API call
            const response = await fetch('/api/search-suggestions');
            if (response.ok) {
                this.searchData = await response.json();
            }
        } catch (error) {
            console.log('Using fallback search data');
            // Fallback data extraction from current page
            this.extractDataFromPage();
        }
    }

    extractDataFromPage() {
        // Extract agents from current table
        const agentCells = document.querySelectorAll('table tbody tr td:nth-child(2)');
        const agents = new Set();
        agentCells.forEach(cell => {
            const agent = cell.textContent.trim();
            if (agent && agent !== 'TBA') {
                agents.add(agent);
            }
        });
        this.searchData.agents = Array.from(agents);

        // Extract request numbers
        const requestCells = document.querySelectorAll('.request-number');
        const requests = new Set();
        requestCells.forEach(cell => {
            const request = cell.textContent.trim();
            if (request) {
                requests.add(request);
            }
        });
        this.searchData.requestNumbers = Array.from(requests);

        // Extract nationalities
        const nationalityCells = document.querySelectorAll('table tbody tr td:nth-child(4)');
        const nationalities = new Set();
        nationalityCells.forEach(cell => {
            const nationality = cell.textContent.trim();
            if (nationality && nationality !== 'TBA') {
                nationalities.add(nationality);
            }
        });
        this.searchData.nationalities = Array.from(nationalities);
    }

    setupAutocomplete() {
        // Setup autocomplete for agent field
        const agentInput = document.querySelector('input[name="agent"]');
        if (agentInput) {
            this.createAutocomplete(agentInput, this.searchData.agents, 'agents');
        }

        // Setup autocomplete for request number field
        const requestInput = document.querySelector('input[name="request_number"]');
        if (requestInput) {
            this.createAutocomplete(requestInput, this.searchData.requestNumbers, 'requests');
        }

        // Add smart suggestion for common search patterns
        this.addSmartSuggestions();
    }

    createAutocomplete(input, data, type) {
        const wrapper = document.createElement('div');
        wrapper.className = 'autocomplete-wrapper';
        wrapper.style.position = 'relative';
        
        // Wrap the input
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 2px solid #ffb700;
            border-top: none;
            border-radius: 0 0 8px 8px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 4px 12px rgba(255, 183, 0, 0.2);
        `;
        wrapper.appendChild(dropdown);

        input.addEventListener('input', (e) => {
            const value = e.target.value.toLowerCase();
            if (value.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            const matches = data.filter(item => 
                item.toLowerCase().includes(value)
            ).slice(0, 8); // Limit to 8 suggestions

            if (matches.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            dropdown.innerHTML = matches.map(match => 
                `<div class="autocomplete-item" style="
                    padding: 10px 15px;
                    cursor: pointer;
                    border-bottom: 1px solid #f1f3f5;
                    transition: all 0.2s;
                " data-value="${match}">
                    ${this.highlightMatch(match, value)}
                </div>`
            ).join('');

            dropdown.style.display = 'block';

            // Add click listeners to items
            dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('mouseenter', () => {
                    item.style.background = 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)';
                    item.style.color = '#333';
                });
                item.addEventListener('mouseleave', () => {
                    item.style.background = 'white';
                    item.style.color = 'inherit';
                });
                item.addEventListener('click', () => {
                    input.value = item.dataset.value;
                    dropdown.style.display = 'none';
                    input.focus();
                });
            });
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Handle keyboard navigation
        input.addEventListener('keydown', (e) => {
            const items = dropdown.querySelectorAll('.autocomplete-item');
            const activeItem = dropdown.querySelector('.autocomplete-item.active');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const current = activeItem || items[0];
                if (current) {
                    if (activeItem) activeItem.classList.remove('active');
                    const next = current.nextElementSibling || items[0];
                    next.classList.add('active');
                    next.scrollIntoView({block: 'nearest'});
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const current = activeItem || items[items.length - 1];
                if (current) {
                    if (activeItem) activeItem.classList.remove('active');
                    const prev = current.previousElementSibling || items[items.length - 1];
                    prev.classList.add('active');
                    prev.scrollIntoView({block: 'nearest'});
                }
            } else if (e.key === 'Enter') {
                if (activeItem) {
                    e.preventDefault();
                    activeItem.click();
                }
            } else if (e.key === 'Escape') {
                dropdown.style.display = 'none';
            }
        });
    }

    highlightMatch(text, query) {
        const index = text.toLowerCase().indexOf(query);
        if (index === -1) return text;
        
        return text.substring(0, index) + 
               `<strong style="color: #333; background-color: #FFD700; padding: 1px 2px; border-radius: 2px;">` +
               text.substring(index, index + query.length) + 
               '</strong>' + 
               text.substring(index + query.length);
    }

    addSmartSuggestions() {
        // Add placeholder hints for better UX
        const requestInput = document.querySelector('input[name="request_number"]');
        if (requestInput && !requestInput.placeholder.includes('INB-')) {
            requestInput.placeholder = 'e.g., INB-202501-0001';
        }

        const agentInput = document.querySelector('input[name="agent"]');
        if (agentInput && !agentInput.placeholder.includes('type')) {
            agentInput.placeholder = 'Start typing agent name...';
        }

        // Add instant search capability
        const searchBtn = document.querySelector('.btn-search');
        if (searchBtn) {
            const form = searchBtn.closest('form');
            let searchTimeout;
            
            form.querySelectorAll('input, select').forEach(field => {
                field.addEventListener('input', () => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        // Auto-submit if user has typed something substantial
                        const hasContent = Array.from(form.querySelectorAll('input, select'))
                            .some(f => f.value.trim().length > 2);
                        
                        if (hasContent) {
                            // Optional: Auto-submit after 1 second of no typing
                            // form.submit();
                        }
                    }, 1000);
                });
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SmartSearch();
});