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
        suggestionsContainer.style.border = 'none';
        suggestionsContainer.style.borderRadius = '8px';
        suggestionsContainer.style.maxHeight = '350px';
        suggestionsContainer.style.overflowY = 'auto';
        suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
        suggestionsContainer.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
        
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
                // Get suggestions from specific hotel names (highest priority)
                const hotelSuggestions = HOTEL_NAMES.filter(hotel => 
                    hotel.name.toLowerCase().includes(query)
                ).map(hotel => ({
                    text: hotel.name,
                    type: 'hotel'
                }));
                
                // Get suggestions from hotel chains (medium priority)
                const chainSuggestions = HOTEL_CHAINS.filter(chain => 
                    chain.name.toLowerCase().includes(query)
                ).map(chain => ({
                    text: chain.name,
                    type: 'chain'
                }));
                
                // Get suggestions from cities (lowest priority)
                const citySuggestions = HOTEL_CITIES.filter(city => 
                    city.name.toLowerCase().includes(query)
                ).map(city => ({
                    text: city.name,
                    type: 'city'
                }));
                
                // Combine suggestions, putting specific hotels first, then chains, then cities
                const suggestions = [...hotelSuggestions, ...chainSuggestions, ...citySuggestions];
                
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
                
                // Add headings for each category if needed
                let hasAddedHotelHeading = false;
                let hasAddedChainHeading = false;
                let hasAddedCityHeading = false;
                
                limitedSuggestions.forEach((suggestion, index) => {
                    // Add headings before the first item of each type
                    if (suggestion.type === 'hotel' && !hasAddedHotelHeading) {
                        hasAddedHotelHeading = true;
                        const hotelHeading = document.createElement('div');
                        hotelHeading.className = 'autocomplete-heading';
                        hotelHeading.textContent = 'Specific Hotels';
                        hotelHeading.style.padding = '10px 15px';
                        hotelHeading.style.fontWeight = 'bold';
                        hotelHeading.style.backgroundColor = '#fffaf0';
                        hotelHeading.style.fontSize = '0.9em';
                        hotelHeading.style.color = '#664d03';
                        hotelHeading.style.borderBottom = '1px solid rgba(0,0,0,0.05)';
                        suggestionsContainer.appendChild(hotelHeading);
                    } else if (suggestion.type === 'chain' && !hasAddedChainHeading) {
                        hasAddedChainHeading = true;
                        const chainHeading = document.createElement('div');
                        chainHeading.className = 'autocomplete-heading';
                        chainHeading.textContent = 'Hotel Chains';
                        chainHeading.style.padding = '10px 15px';
                        chainHeading.style.fontWeight = 'bold';
                        chainHeading.style.backgroundColor = '#fff8e1';
                        chainHeading.style.fontSize = '0.9em';
                        chainHeading.style.color = '#664d03';
                        chainHeading.style.borderBottom = '1px solid rgba(0,0,0,0.05)';
                        suggestionsContainer.appendChild(chainHeading);
                    } else if (suggestion.type === 'city' && !hasAddedCityHeading) {
                        hasAddedCityHeading = true;
                        const cityHeading = document.createElement('div');
                        cityHeading.className = 'autocomplete-heading';
                        cityHeading.textContent = 'Cities';
                        cityHeading.style.padding = '10px 15px';
                        cityHeading.style.fontWeight = 'bold';
                        cityHeading.style.backgroundColor = '#fff3cd';
                        cityHeading.style.fontSize = '0.9em';
                        cityHeading.style.color = '#664d03';
                        cityHeading.style.borderBottom = '1px solid rgba(0,0,0,0.05)';
                        suggestionsContainer.appendChild(cityHeading);
                    }
                    
                    const suggestionElement = document.createElement('div');
                    suggestionElement.className = 'autocomplete-suggestion';
                    suggestionElement.style.padding = '10px 15px';
                    suggestionElement.style.cursor = 'pointer';
                    suggestionElement.style.transition = 'all 0.2s ease';
                    suggestionElement.style.borderLeft = '3px solid transparent';
                    
                    // Add an icon based on the type with yellow color scheme
                    let iconColor, iconClass, gradientBg;
                    if (suggestion.type === 'hotel') {
                        iconClass = 'fa-hotel';
                        iconColor = '#f0ad4e'; // Warm yellow for hotels
                        gradientBg = 'linear-gradient(to right, #fff8e1, #ffffff)';
                    } else if (suggestion.type === 'chain') {
                        iconClass = 'fa-building';
                        iconColor = '#ff9800'; // Orange for chains
                        gradientBg = 'linear-gradient(to right, #fff3cd, #ffffff)';
                    } else {
                        iconClass = 'fa-map-marker-alt';
                        iconColor = '#e67e22'; // Darker orange for cities
                        gradientBg = 'linear-gradient(to right, #ffe9c2, #ffffff)';
                    }
                    
                    // Create enhanced suggestion content with styled icon
                    suggestionElement.innerHTML = 
                        `<div style="display: flex; align-items: center;">
                            <div style="width: 30px; height: 30px; border-radius: 50%; 
                                      background-color: ${iconColor}20; 
                                      display: flex; align-items: center; justify-content: center; 
                                      margin-right: 10px;">
                                <i class="fas ${iconClass}" style="color: ${iconColor};"></i>
                            </div>
                            <span>${suggestion.text}</span>
                        </div>`;
                    
                    // Highlight on hover with gradient effect
                    suggestionElement.addEventListener('mouseover', function() {
                        this.style.borderLeft = `3px solid ${iconColor}`;
                        this.style.backgroundColor = '#fffbea';
                        this.style.backgroundImage = gradientBg;
                        selectedIndex = index;
                        highlightSuggestion();
                    });
                    
                    suggestionElement.addEventListener('mouseout', function() {
                        this.style.borderLeft = '3px solid transparent';
                        this.style.backgroundColor = '';
                        this.style.backgroundImage = '';
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