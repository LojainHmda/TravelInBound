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
        // Load suggestions first; setupAutocomplete used a stale empty list if run immediately (race).
        this.loadSearchData().then(() => this.setupAutocomplete());
    }

    async loadSearchData() {
        try {
            const response = await fetch('/api/search-suggestions', { credentials: 'same-origin' });
            if (response.ok) {
                const raw = await response.json();
                this.searchData.agents = Array.isArray(raw.agents) ? raw.agents.filter(Boolean) : [];
                this.searchData.requestNumbers = Array.isArray(raw.requestNumbers) ? raw.requestNumbers.filter(Boolean) : [];
                this.searchData.nationalities = Array.isArray(raw.nationalities) ? raw.nationalities.filter(Boolean) : [];
            } else {
                this.extractDataFromPage();
            }
        } catch (error) {
            console.log('Using fallback search data', error);
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
        const agentInput = document.querySelector('input[name="agent"]');
        if (agentInput && !agentInput.dataset.autocompleteBound) {
            agentInput.dataset.autocompleteBound = '1';
            this.createAutocomplete(agentInput, () => this.searchData.agents);
        }

        const requestInput = document.querySelector('input[name="request_number"]');
        if (requestInput && !requestInput.dataset.autocompleteBound) {
            requestInput.dataset.autocompleteBound = '1';
            this.createAutocomplete(requestInput, () => this.searchData.requestNumbers);
        }

        this.addSmartSuggestions();
    }

    createAutocomplete(input, getDataFn) {
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
            const q = (e.target.value || '').trim().toLowerCase();
            const data = (getDataFn.call(this) || []).map((s) => String(s).trim()).filter(Boolean);

            if (q.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            const matches = data
                .filter((item) => item.toLowerCase().includes(q))
                .slice(0, 15);

            if (matches.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            dropdown.innerHTML = '';
            matches.forEach((match) => {
                const row = document.createElement('div');
                row.className = 'autocomplete-item';
                row.style.cssText =
                    'padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #f1f3f5; transition: all 0.2s;';
                row.dataset.value = match;
                row.innerHTML = this.highlightMatch(match, q);
                row.addEventListener('mouseenter', () => {
                    row.style.background = 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)';
                    row.style.color = '#333';
                });
                row.addEventListener('mouseleave', () => {
                    row.style.background = 'white';
                    row.style.color = 'inherit';
                });
                row.addEventListener('click', () => {
                    input.value = row.dataset.value;
                    dropdown.style.display = 'none';
                    input.focus();
                });
                dropdown.appendChild(row);
            });

            dropdown.style.display = 'block';
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

    escapeHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    highlightMatch(text, queryLower) {
        const t = String(text);
        const lower = t.toLowerCase();
        const index = lower.indexOf(queryLower);
        if (index === -1) return this.escapeHtml(t);

        const before = this.escapeHtml(t.substring(0, index));
        const mid = this.escapeHtml(t.substring(index, index + queryLower.length));
        const after = this.escapeHtml(t.substring(index + queryLower.length));
        return (
            before +
            '<strong style="color: #333; background-color: #FFD700; padding: 1px 2px; border-radius: 2px;">' +
            mid +
            '</strong>' +
            after
        );
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