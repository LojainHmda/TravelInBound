/**
 * Flight confirmation form autocomplete functionality
 * Provides autocomplete for airlines and airports using static data
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Flight autocomplete script loaded');

    // Elements to add autocomplete to
    const airlineInput = document.querySelector('input[name="airline"]');
    const departureAirportInput = document.querySelector('input[name="departure_airport"]');
    const arrivalAirportInput = document.querySelector('input[name="arrival_airport"]');
    
    if (airlineInput) {
        setupAirlineAutocomplete(airlineInput);
    }
    
    if (departureAirportInput) {
        setupAirportAutocomplete(departureAirportInput);
    }
    
    if (arrivalAirportInput) {
        setupAirportAutocomplete(arrivalAirportInput);
    }
    
    /**
     * Set up autocomplete for airline field
     */
    function setupAirlineAutocomplete(inputElement) {
        // Create a container for suggestions
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'autocomplete-suggestions';
        suggestionsContainer.style.display = 'none';
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.zIndex = '1000';
        suggestionsContainer.style.backgroundColor = '#fff';
        suggestionsContainer.style.border = '1px solid #ddd';
        suggestionsContainer.style.maxHeight = '200px';
        suggestionsContainer.style.overflowY = 'auto';
        suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
        
        // Add container after the input
        inputElement.parentNode.insertBefore(suggestionsContainer, inputElement.nextSibling);
        
        // Keep track of selected suggestion index
        let selectedIndex = -1;
        
        // Input event listener to search for suggestions
        inputElement.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            
            if (query.length < 1) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            try {
                // Search through static airline data (defined in flight_autocomplete_data.js)
                const airlines = AIRLINE_DATA.filter(airline => 
                    airline.code.toLowerCase().includes(query) || 
                    airline.name.toLowerCase().includes(query)
                );
                
                // Clear and hide suggestions if no results
                if (!airlines || airlines.length === 0) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                // Populate suggestions
                suggestionsContainer.innerHTML = '';
                airlines.forEach((airline, index) => {
                    const suggestion = document.createElement('div');
                    suggestion.className = 'autocomplete-suggestion';
                    suggestion.textContent = `${airline.code} - ${airline.name}`;
                    suggestion.style.padding = '8px';
                    suggestion.style.cursor = 'pointer';
                    
                    // Highlight on hover
                    suggestion.addEventListener('mouseover', function() {
                        this.style.backgroundColor = '#f0f0f0';
                        selectedIndex = index;
                        highlightSuggestion();
                    });
                    
                    suggestion.addEventListener('mouseout', function() {
                        this.style.backgroundColor = '';
                    });
                    
                    // Select on click
                    suggestion.addEventListener('click', function() {
                        inputElement.value = airline.code;
                        suggestionsContainer.style.display = 'none';
                    });
                    
                    suggestionsContainer.appendChild(suggestion);
                });
                
                // Show suggestions
                suggestionsContainer.style.display = 'block';
                suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
                selectedIndex = -1;
                
            } catch (error) {
                console.error('Error processing airline data:', error);
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
            }
        });
        
        // Handle keyboard navigation
        inputElement.addEventListener('keydown', function(e) {
            const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
            
            if (suggestionsContainer.style.display === 'none') {
                return;
            }
            
            // Down arrow
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex < suggestions.length - 1) ? selectedIndex + 1 : 0;
                highlightSuggestion();
            }
            // Up arrow
            else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex > 0) ? selectedIndex - 1 : suggestions.length - 1;
                highlightSuggestion();
            }
            // Enter
            else if (e.key === 'Enter' && selectedIndex !== -1) {
                e.preventDefault();
                suggestions[selectedIndex].click();
            }
            // Escape
            else if (e.key === 'Escape') {
                suggestionsContainer.style.display = 'none';
                selectedIndex = -1;
            }
        });
        
        // Highlight the selected suggestion
        function highlightSuggestion() {
            const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
            
            suggestions.forEach((suggestion, index) => {
                if (index === selectedIndex) {
                    suggestion.style.backgroundColor = '#f0f0f0';
                } else {
                    suggestion.style.backgroundColor = '';
                }
            });
            
            // Scroll to the selected suggestion if needed
            if (selectedIndex !== -1) {
                const selected = suggestions[selectedIndex];
                const containerTop = suggestionsContainer.scrollTop;
                const containerBottom = containerTop + suggestionsContainer.offsetHeight;
                const elemTop = selected.offsetTop;
                const elemBottom = elemTop + selected.offsetHeight;
                
                if (elemTop < containerTop) {
                    suggestionsContainer.scrollTop = elemTop;
                } else if (elemBottom > containerBottom) {
                    suggestionsContainer.scrollTop = elemBottom - suggestionsContainer.offsetHeight;
                }
            }
        }
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== inputElement && e.target !== suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
        });
    }
    
    /**
     * Set up autocomplete for airport fields
     */
    function setupAirportAutocomplete(inputElement) {
        // Create a container for suggestions
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'autocomplete-suggestions';
        suggestionsContainer.style.display = 'none';
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.zIndex = '1000';
        suggestionsContainer.style.backgroundColor = '#fff';
        suggestionsContainer.style.border = '1px solid #ddd';
        suggestionsContainer.style.maxHeight = '200px';
        suggestionsContainer.style.overflowY = 'auto';
        suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
        
        // Add container after the input
        inputElement.parentNode.insertBefore(suggestionsContainer, inputElement.nextSibling);
        
        // Keep track of selected suggestion index
        let selectedIndex = -1;
        
        // Input event listener to search for suggestions
        inputElement.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            
            if (query.length < 1) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            try {
                // Search through static airport data (defined in flight_autocomplete_data.js)
                const airports = AIRPORT_DATA.filter(airport => 
                    airport.code.toLowerCase().includes(query) || 
                    airport.name.toLowerCase().includes(query)
                );
                
                // Clear and hide suggestions if no results
                if (!airports || airports.length === 0) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                // Populate suggestions
                suggestionsContainer.innerHTML = '';
                airports.forEach((airport, index) => {
                    const suggestion = document.createElement('div');
                    suggestion.className = 'autocomplete-suggestion';
                    suggestion.textContent = `${airport.code} - ${airport.name}`;
                    suggestion.style.padding = '8px';
                    suggestion.style.cursor = 'pointer';
                    
                    // Highlight on hover
                    suggestion.addEventListener('mouseover', function() {
                        this.style.backgroundColor = '#f0f0f0';
                        selectedIndex = index;
                        highlightSuggestion();
                    });
                    
                    suggestion.addEventListener('mouseout', function() {
                        this.style.backgroundColor = '';
                    });
                    
                    // Select on click
                    suggestion.addEventListener('click', function() {
                        inputElement.value = airport.code;
                        suggestionsContainer.style.display = 'none';
                    });
                    
                    suggestionsContainer.appendChild(suggestion);
                });
                
                // Show suggestions
                suggestionsContainer.style.display = 'block';
                suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
                selectedIndex = -1;
                
            } catch (error) {
                console.error('Error processing airport data:', error);
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
            }
        });
        
        // Handle keyboard navigation
        inputElement.addEventListener('keydown', function(e) {
            const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
            
            if (suggestionsContainer.style.display === 'none') {
                return;
            }
            
            // Down arrow
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex < suggestions.length - 1) ? selectedIndex + 1 : 0;
                highlightSuggestion();
            }
            // Up arrow
            else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex > 0) ? selectedIndex - 1 : suggestions.length - 1;
                highlightSuggestion();
            }
            // Enter
            else if (e.key === 'Enter' && selectedIndex !== -1) {
                e.preventDefault();
                suggestions[selectedIndex].click();
            }
            // Escape
            else if (e.key === 'Escape') {
                suggestionsContainer.style.display = 'none';
                selectedIndex = -1;
            }
        });
        
        // Highlight the selected suggestion
        function highlightSuggestion() {
            const suggestions = suggestionsContainer.querySelectorAll('.autocomplete-suggestion');
            
            suggestions.forEach((suggestion, index) => {
                if (index === selectedIndex) {
                    suggestion.style.backgroundColor = '#f0f0f0';
                } else {
                    suggestion.style.backgroundColor = '';
                }
            });
            
            // Scroll to the selected suggestion if needed
            if (selectedIndex !== -1) {
                const selected = suggestions[selectedIndex];
                const containerTop = suggestionsContainer.scrollTop;
                const containerBottom = containerTop + suggestionsContainer.offsetHeight;
                const elemTop = selected.offsetTop;
                const elemBottom = elemTop + selected.offsetHeight;
                
                if (elemTop < containerTop) {
                    suggestionsContainer.scrollTop = elemTop;
                } else if (elemBottom > containerBottom) {
                    suggestionsContainer.scrollTop = elemBottom - suggestionsContainer.offsetHeight;
                }
            }
        }
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== inputElement && e.target !== suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
        });
    }
});