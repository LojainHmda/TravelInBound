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
        suggestionsContainer.style.borderRadius = '12px';
        suggestionsContainer.style.maxHeight = '400px';
        suggestionsContainer.style.overflowY = 'auto';
        suggestionsContainer.style.width = inputElement.offsetWidth + 'px';
        suggestionsContainer.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.15)';
        suggestionsContainer.style.padding = '8px';
        suggestionsContainer.style.background = 'linear-gradient(to bottom, #fffbf2, #fff)';
        // Add custom scrollbar styling
        suggestionsContainer.style.scrollbarWidth = 'thin';
        suggestionsContainer.style.scrollbarColor = '#FFA500 #f5f5f5';
        
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
                        hotelHeading.innerHTML = '<i class="fas fa-hotel me-2"></i> Specific Hotels';
                        hotelHeading.style.padding = '10px 15px';
                        hotelHeading.style.fontWeight = 'bold';
                        hotelHeading.style.margin = '8px 0 2px 0';
                        hotelHeading.style.fontSize = '0.9em';
                        hotelHeading.style.color = '#FFA500';
                        hotelHeading.style.borderBottom = '2px solid #FFD700';
                        suggestionsContainer.appendChild(hotelHeading);
                    } else if (suggestion.type === 'chain' && !hasAddedChainHeading) {
                        hasAddedChainHeading = true;
                        const chainHeading = document.createElement('div');
                        chainHeading.className = 'autocomplete-heading';
                        chainHeading.innerHTML = '<i class="fas fa-building me-2"></i> Hotel Chains';
                        chainHeading.style.padding = '10px 15px';
                        chainHeading.style.fontWeight = 'bold';
                        chainHeading.style.margin = '8px 0 2px 0';
                        chainHeading.style.fontSize = '0.9em';
                        chainHeading.style.color = '#FF9500';
                        chainHeading.style.borderBottom = '2px solid #FFCC00';
                        suggestionsContainer.appendChild(chainHeading);
                    } else if (suggestion.type === 'city' && !hasAddedCityHeading) {
                        hasAddedCityHeading = true;
                        const cityHeading = document.createElement('div');
                        cityHeading.className = 'autocomplete-heading';
                        cityHeading.innerHTML = '<i class="fas fa-map-marker-alt me-2"></i> Cities';
                        cityHeading.style.padding = '10px 15px';
                        cityHeading.style.fontWeight = 'bold';
                        cityHeading.style.margin = '8px 0 2px 0';
                        cityHeading.style.fontSize = '0.9em';
                        cityHeading.style.color = '#FF8C00';
                        cityHeading.style.borderBottom = '2px solid #FFB347';
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
                    
                    // Create card-styled suggestions with gradient backgrounds
                    let gradientColors, iconBgColor, borderColor;
                    
                    if (suggestion.type === 'hotel') {
                        gradientColors = 'linear-gradient(135deg, #FFD700, #FFA500)';  // Gold to Orange
                        iconBgColor = '#FFD700';
                        borderColor = '#FFA500';
                    } else if (suggestion.type === 'chain') {
                        gradientColors = 'linear-gradient(135deg, #FFCC00, #FF9500)';  // Yellow to Amber
                        iconBgColor = '#FFCC00';
                        borderColor = '#FF9500';
                    } else {
                        gradientColors = 'linear-gradient(135deg, #FFB347, #FF8C00)';  // Pastel Orange to Dark Orange
                        iconBgColor = '#FFB347';
                        borderColor = '#FF8C00';
                    }
                    
                    // Create card-styled suggestion with gradient background
                    suggestionElement.innerHTML = 
                        `<div style="display: flex; align-items: center; background: ${gradientColors}; 
                                    border-radius: 8px; padding: 8px 12px; margin: 5px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="width: 32px; height: 32px; border-radius: 50%; 
                                      background-color: rgba(255,255,255,0.85); 
                                      display: flex; align-items: center; justify-content: center; 
                                      margin-right: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <i class="fas ${iconClass}" style="color: ${iconColor};"></i>
                            </div>
                            <span style="color: #fff; font-weight: 500; text-shadow: 0 1px 1px rgba(0,0,0,0.1);">${suggestion.text}</span>
                        </div>`;
                    
                    // Enhance on hover with scaling and shadow
                    suggestionElement.addEventListener('mouseover', function() {
                        const card = this.querySelector('div');
                        card.style.transform = 'scale(1.02)';
                        card.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                        card.style.transition = 'all 0.2s ease';
                        selectedIndex = index;
                        highlightSuggestion();
                    });
                    
                    suggestionElement.addEventListener('mouseout', function() {
                        const card = this.querySelector('div');
                        card.style.transform = 'scale(1)';
                        card.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
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