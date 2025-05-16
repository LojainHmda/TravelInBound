/**
 * Hotel confirmation form autocomplete functionality
 * Provides autocomplete for hotel names and cities using static data
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Hotel autocomplete script loaded');

    // Elements to add autocomplete to
    const hotelNameInput = document.querySelector('input[name="hotel_name"]');
    
    if (hotelNameInput) {
        setupHotelAutocomplete(hotelNameInput);
    }
    
    /**
     * Set up autocomplete for hotel name field that combines hotel chains and cities
     */
    function setupHotelAutocomplete(inputElement) {
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
            
            if (query.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            try {
                // Get suggestions from hotel chains
                const chainSuggestions = HOTEL_CHAINS.filter(chain => 
                    chain.name.toLowerCase().includes(query)
                ).map(chain => ({
                    text: chain.name,
                    type: 'chain'
                }));
                
                // Get suggestions from cities
                const citySuggestions = HOTEL_CITIES.filter(city => 
                    city.name.toLowerCase().includes(query)
                ).map(city => ({
                    text: city.name,
                    type: 'city'
                }));
                
                // Combine suggestions, putting hotel chains first
                const suggestions = [...chainSuggestions, ...citySuggestions];
                
                // Limit to 10 suggestions
                const limitedSuggestions = suggestions.slice(0, 10);
                
                // Clear and hide suggestions if no results
                if (limitedSuggestions.length === 0) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                // Populate suggestions
                suggestionsContainer.innerHTML = '';
                
                // Add a heading for chains if there are any
                if (chainSuggestions.length > 0 && citySuggestions.length > 0) {
                    const chainHeading = document.createElement('div');
                    chainHeading.className = 'autocomplete-heading';
                    chainHeading.textContent = 'Hotel Chains';
                    chainHeading.style.padding = '8px 12px';
                    chainHeading.style.fontWeight = 'bold';
                    chainHeading.style.backgroundColor = '#f8f9fa';
                    chainHeading.style.fontSize = '0.8em';
                    suggestionsContainer.appendChild(chainHeading);
                }
                
                limitedSuggestions.forEach((suggestion, index) => {
                    // Add a heading for cities if there are any and we're on the first city
                    if (suggestion.type === 'city' && index > 0 && limitedSuggestions[index-1].type === 'chain') {
                        const cityHeading = document.createElement('div');
                        cityHeading.className = 'autocomplete-heading';
                        cityHeading.textContent = 'Cities';
                        cityHeading.style.padding = '8px 12px';
                        cityHeading.style.fontWeight = 'bold';
                        cityHeading.style.backgroundColor = '#f8f9fa';
                        cityHeading.style.fontSize = '0.8em';
                        suggestionsContainer.appendChild(cityHeading);
                    }
                    
                    const suggestionElement = document.createElement('div');
                    suggestionElement.className = 'autocomplete-suggestion';
                    suggestionElement.textContent = suggestion.text;
                    suggestionElement.style.padding = '8px 12px';
                    suggestionElement.style.cursor = 'pointer';
                    
                    // Add an icon based on the type
                    if (suggestion.type === 'chain') {
                        suggestionElement.innerHTML = '<i class="fas fa-building mr-2"></i> ' + suggestion.text;
                    } else {
                        suggestionElement.innerHTML = '<i class="fas fa-map-marker-alt mr-2"></i> ' + suggestion.text;
                    }
                    
                    // Highlight on hover
                    suggestionElement.addEventListener('mouseover', function() {
                        this.style.backgroundColor = '#f0f0f0';
                        selectedIndex = index;
                        highlightSuggestion();
                    });
                    
                    suggestionElement.addEventListener('mouseout', function() {
                        this.style.backgroundColor = '';
                    });
                    
                    // Select on click
                    suggestionElement.addEventListener('click', function() {
                        let selectedText = suggestion.text;
                        
                        // For chains, add "Hotels" after the chain name if not already present
                        if (suggestion.type === 'chain' && !selectedText.toLowerCase().includes('hotel')) {
                            selectedText += ' Hotel';
                        }
                        
                        // For cities, prepend a common hotel naming pattern
                        if (suggestion.type === 'city') {
                            const cityName = suggestion.text.split(',')[0].trim();
                            selectedText = 'Hotel in ' + cityName;
                        }
                        
                        inputElement.value = selectedText;
                        suggestionsContainer.style.display = 'none';
                    });
                    
                    suggestionsContainer.appendChild(suggestionElement);
                });
                
                // Show suggestions
                suggestionsContainer.style.display = 'block';
                suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
                selectedIndex = -1;
                
            } catch (error) {
                console.error('Error processing hotel data:', error);
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