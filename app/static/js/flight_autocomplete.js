/**
 * Flight confirmation form autocomplete functionality
 * Provides autocomplete for airlines and airports using static data
 * Updated for multi-segment support with global function access
 */

console.log('🔧 Flight autocomplete script loaded');

/**
 * Set up autocomplete for airline field
 */
function setupAirlineAutocomplete(inputElement) {
    console.log('🛫 Setting up airline autocomplete for:', inputElement.name);
    
    // Check if data is available
    if (typeof airlines === 'undefined') {
        console.error('❌ Airlines data not available for autocomplete');
        return;
    }
    
    // Create suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'autocomplete-suggestions';
    suggestionsContainer.style.cssText = `
        display: none;
        position: absolute;
        z-index: 1000;
        background-color: #fff;
        border: 1px solid #ddd;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    `;
    
    // Add container after the input
    inputElement.parentNode.appendChild(suggestionsContainer);
    
    let selectedIndex = -1;
    
    // Input event listener
    inputElement.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        
        if (query.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        try {
            console.log('🔍 Airlines array check:', typeof airlines, airlines ? airlines.length : 'undefined');
            
            // Filter airlines
            const filteredAirlines = airlines.filter(airline => 
                airline.code.toLowerCase().includes(query) || 
                airline.name.toLowerCase().includes(query)
            ).slice(0, 10);
            
            console.log('🎯 Filtered airlines for query "' + query + '":', filteredAirlines.length);
            
            if (filteredAirlines.length === 0) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            // Create suggestions
            suggestionsContainer.innerHTML = '';
            filteredAirlines.forEach((airline, index) => {
                const suggestion = document.createElement('div');
                suggestion.className = 'autocomplete-suggestion';
                suggestion.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;';
                suggestion.textContent = `${airline.code} - ${airline.name}`;
                
                // Hover effects
                suggestion.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#f0f0f0';
                    selectedIndex = index;
                });
                
                suggestion.addEventListener('mouseout', function() {
                    this.style.backgroundColor = '';
                });
                
                // Click to select
                suggestion.addEventListener('click', function() {
                    inputElement.value = airline.code;
                    suggestionsContainer.style.display = 'none';
                    inputElement.focus();
                });
                
                suggestionsContainer.appendChild(suggestion);
            });
            
            // Position and show
            suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
            suggestionsContainer.style.display = 'block';
            selectedIndex = -1;
            
        } catch (error) {
            console.error('❌ Error in airline autocomplete:', error);
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Keyboard navigation
    inputElement.addEventListener('keydown', function(e) {
        const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
        
        if (suggestionsContainer.style.display === 'none' || suggestions.length === 0) {
            return;
        }
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
            updateSelection(suggestions);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(suggestions);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0) {
                suggestions[selectedIndex].click();
            }
        } else if (e.key === 'Escape') {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Close suggestions on outside click
    document.addEventListener('click', function(e) {
        if (!inputElement.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    function updateSelection(suggestions) {
        suggestions.forEach((suggestion, index) => {
            suggestion.style.backgroundColor = index === selectedIndex ? '#007bff' : '';
            suggestion.style.color = index === selectedIndex ? 'white' : '';
        });
    }
    
    console.log('✅ Airline autocomplete initialized');
}

/**
 * Set up autocomplete for airport field
 */
function setupAirportAutocomplete(inputElement) {
    console.log('🛬 Setting up airport autocomplete for:', inputElement.name);
    
    // Check if data is available
    if (typeof airports === 'undefined') {
        console.error('❌ Airports data not available for autocomplete');
        return;
    }
    
    // Create suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'autocomplete-suggestions';
    suggestionsContainer.style.cssText = `
        display: none;
        position: absolute;
        z-index: 1000;
        background-color: #fff;
        border: 1px solid #ddd;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    `;
    
    // Add container after the input
    inputElement.parentNode.appendChild(suggestionsContainer);
    
    let selectedIndex = -1;
    
    // Input event listener
    inputElement.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        
        if (query.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        try {
            // Filter airports
            const filteredAirports = airports.filter(airport => 
                airport.code.toLowerCase().includes(query) || 
                airport.name.toLowerCase().includes(query) ||
                (airport.city && airport.city.toLowerCase().includes(query))
            ).slice(0, 10);
            
            if (filteredAirports.length === 0) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            // Create suggestions
            suggestionsContainer.innerHTML = '';
            filteredAirports.forEach((airport, index) => {
                const suggestion = document.createElement('div');
                suggestion.className = 'autocomplete-suggestion';
                suggestion.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;';
                
                const displayText = airport.city ? 
                    `${airport.code} - ${airport.name}, ${airport.city}` : 
                    `${airport.code} - ${airport.name}`;
                suggestion.textContent = displayText;
                
                // Hover effects
                suggestion.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#f0f0f0';
                    selectedIndex = index;
                });
                
                suggestion.addEventListener('mouseout', function() {
                    this.style.backgroundColor = '';
                });
                
                // Click to select
                suggestion.addEventListener('click', function() {
                    inputElement.value = airport.code;
                    suggestionsContainer.style.display = 'none';
                    inputElement.focus();
                });
                
                suggestionsContainer.appendChild(suggestion);
            });
            
            // Position and show
            suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
            suggestionsContainer.style.display = 'block';
            selectedIndex = -1;
            
        } catch (error) {
            console.error('❌ Error in airport autocomplete:', error);
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Keyboard navigation
    inputElement.addEventListener('keydown', function(e) {
        const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
        
        if (suggestionsContainer.style.display === 'none' || suggestions.length === 0) {
            return;
        }
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
            updateSelection(suggestions);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(suggestions);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0) {
                suggestions[selectedIndex].click();
            }
        } else if (e.key === 'Escape') {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Close suggestions on outside click
    document.addEventListener('click', function(e) {
        if (!inputElement.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    function updateSelection(suggestions) {
        suggestions.forEach((suggestion, index) => {
            suggestion.style.backgroundColor = index === selectedIndex ? '#007bff' : '';
            suggestion.style.color = index === selectedIndex ? 'white' : '';
        });
    }
    
    console.log('✅ Airport autocomplete initialized');
}

// Make functions globally available
window.setupAirlineAutocomplete = setupAirlineAutocomplete;
window.setupAirportAutocomplete = setupAirportAutocomplete;

console.log('🚀 Flight autocomplete functions ready globally');