/**
 * Static hotel cities, hotel chains, and specific hotel names data for autocomplete functionality
 * This provides offline data that doesn't require API calls
 */
const HOTEL_CITIES = [
    { code: "AMS", name: "Amsterdam, Netherlands" },
    { code: "ATH", name: "Athens, Greece" },
    { code: "BCN", name: "Barcelona, Spain" },
    { code: "BKK", name: "Bangkok, Thailand" },
    { code: "BER", name: "Berlin, Germany" },
    { code: "BRU", name: "Brussels, Belgium" },
    { code: "BUD", name: "Budapest, Hungary" },
    { code: "CAI", name: "Cairo, Egypt" },
    { code: "CPH", name: "Copenhagen, Denmark" },
    { code: "DEL", name: "Delhi, India" },
    { code: "DXB", name: "Dubai, UAE" },
    { code: "FRA", name: "Frankfurt, Germany" },
    { code: "HKG", name: "Hong Kong" },
    { code: "IST", name: "Istanbul, Turkey" },
    { code: "JKT", name: "Jakarta, Indonesia" },
    { code: "JNB", name: "Johannesburg, South Africa" },
    { code: "KUL", name: "Kuala Lumpur, Malaysia" },
    { code: "LIS", name: "Lisbon, Portugal" },
    { code: "LON", name: "London, United Kingdom" },
    { code: "MAD", name: "Madrid, Spain" },
    { code: "MEL", name: "Melbourne, Australia" },
    { code: "MEX", name: "Mexico City, Mexico" },
    { code: "MIL", name: "Milan, Italy" },
    { code: "MNL", name: "Manila, Philippines" },
    { code: "MOW", name: "Moscow, Russia" },
    { code: "MUC", name: "Munich, Germany" },
    { code: "NYC", name: "New York, USA" },
    { code: "OSL", name: "Oslo, Norway" },
    { code: "PAR", name: "Paris, France" },
    { code: "PRG", name: "Prague, Czech Republic" },
    { code: "RIO", name: "Rio de Janeiro, Brazil" },
    { code: "ROM", name: "Rome, Italy" },
    { code: "SEL", name: "Seoul, South Korea" },
    { code: "SFO", name: "San Francisco, USA" },
    { code: "SGN", name: "Ho Chi Minh City, Vietnam" },
    { code: "SIN", name: "Singapore" },
    { code: "STO", name: "Stockholm, Sweden" },
    { code: "SYD", name: "Sydney, Australia" },
    { code: "TPE", name: "Taipei, Taiwan" },
    { code: "TYO", name: "Tokyo, Japan" },
    { code: "VIE", name: "Vienna, Austria" },
    { code: "WAW", name: "Warsaw, Poland" },
    { code: "ZRH", name: "Zurich, Switzerland" },
    // Middle East cities
    { code: "AMM", name: "Amman, Jordan" },
    { code: "BEY", name: "Beirut, Lebanon" },
    { code: "DOH", name: "Doha, Qatar" },
    { code: "JED", name: "Jeddah, Saudi Arabia" },
    { code: "RUH", name: "Riyadh, Saudi Arabia" },
    { code: "TLV", name: "Tel Aviv, Israel" }
];

const HOTEL_CHAINS = [
    { code: "ACC", name: "Accor Hotels" },
    { code: "BW", name: "Best Western" },
    { code: "CHI", name: "Choice Hotels International" },
    { code: "HIL", name: "Hilton Hotels" },
    { code: "HYA", name: "Hyatt Hotels" },
    { code: "IHG", name: "InterContinental Hotels Group" },
    { code: "MAR", name: "Marriott International" },
    { code: "RAD", name: "Radisson Hotel Group" },
    { code: "WYN", name: "Wyndham Hotels & Resorts" },
    { code: "FOU", name: "Four Seasons Hotels and Resorts" },
    { code: "RIT", name: "Ritz-Carlton" },
    { code: "JWM", name: "JW Marriott" },
    { code: "SHE", name: "Sheraton Hotels and Resorts" },
    { code: "WES", name: "Westin Hotels & Resorts" },
    { code: "HAM", name: "Hampton by Hilton" },
    { code: "COU", name: "Courtyard by Marriott" },
    { code: "HOL", name: "Holiday Inn" },
    { code: "CRO", name: "Crowne Plaza" },
    { code: "REG", name: "Regent Hotels & Resorts" },
    { code: "SIX", name: "Six Senses Hotels Resorts Spas" },
    { code: "KEM", name: "Kempinski Hotels" },
    { code: "MAN", name: "Mandarin Oriental Hotel Group" },
    { code: "SHA", name: "Shangri-La Hotels and Resorts" },
    { code: "ROS", name: "Rosewood Hotels & Resorts" },
    { code: "AMA", name: "Aman Resorts" },
    // Regional hotel chains
    { code: "ROT", name: "Rotana Hotels" },
    { code: "JUM", name: "Jumeirah Hotels & Resorts" },
    { code: "MEI", name: "Meininger Hotels" },
    { code: "MVM", name: "Movenpick Hotels & Resorts" },
    { code: "PUL", name: "Pullman Hotels" }
];

// Specific hotel names by region and city
const HOTEL_NAMES = [
    // Dubai Hotels
    { code: "BHD", name: "Burj Al Arab Hotel, Dubai" },
    { code: "ATD", name: "Atlantis The Palm, Dubai" },
    { code: "JBH", name: "Jumeirah Beach Hotel, Dubai" },
    { code: "ARM", name: "Armani Hotel Dubai" },
    { code: "PFD", name: "Palace Downtown, Dubai" },
    { code: "MED", name: "Meydan Hotel, Dubai" },
    { code: "KHD", name: "Kempinski Hotel Mall of the Emirates, Dubai" },
    { code: "ROD", name: "Rotana Al Murooj, Dubai" },
    
    // London Hotels
    { code: "SAV", name: "The Savoy, London" },
    { code: "RITT", name: "The Ritz, London" },
    { code: "CLRG", name: "Claridge's, London" },
    { code: "DCHT", name: "Dorchester Hotel, London" },
    { code: "SHR", name: "Shangri-La Hotel at The Shard, London" },
    { code: "JWHM", name: "JW Marriott Grosvenor House, London" },
    
    // New York Hotels
    { code: "PLZA", name: "The Plaza Hotel, New York" },
    { code: "STRS", name: "St. Regis New York" },
    { code: "WALD", name: "The Waldorf Astoria, New York" },
    { code: "PNIN", name: "Peninsula New York" },
    { code: "FOUR", name: "Four Seasons Hotel New York" },
    
    // Paris Hotels
    { code: "RITZ", name: "Ritz Paris" },
    { code: "GPAL", name: "Le Grand Palais, Paris" },
    { code: "SHPA", name: "Shangri-La Hotel, Paris" },
    { code: "FOUP", name: "Four Seasons Hotel George V, Paris" },
    { code: "MAND", name: "Mandarin Oriental Paris" },
    
    // Istanbul Hotels
    { code: "FOUR", name: "Four Seasons Hotel Istanbul at Sultanahmet" },
    { code: "RITZ", name: "The Ritz-Carlton, Istanbul" },
    { code: "CIRG", name: "Ciragan Palace Kempinski, Istanbul" },
    { code: "PARK", name: "Park Hyatt Istanbul" },
    
    // Singapore Hotels
    { code: "MARI", name: "Marina Bay Sands, Singapore" },
    { code: "RAFL", name: "Raffles Hotel, Singapore" },
    { code: "SHAN", name: "Shangri-La Hotel, Singapore" },
    { code: "FULL", name: "The Fullerton Hotel, Singapore" },
    
    // Cairo Hotels
    { code: "SHCA", name: "Sheraton Cairo Hotel & Casino" },
    { code: "FOUC", name: "Four Seasons Hotel Cairo at Nile Plaza" },
    { code: "SOFM", name: "Sofitel Cairo Nile El Gezirah" },
    { code: "MARR", name: "Marriott Mena House, Cairo" },
    { code: "CAIR", name: "Cairo Marriott Hotel & Omar Khayyam Casino" },
    
    // Amman Hotels
    { code: "INTA", name: "InterContinental Amman" },
    { code: "ROTG", name: "Rotana Grand Amman" },
    { code: "KEMP", name: "Kempinski Hotel Amman" },
    { code: "FOUR", name: "Four Seasons Hotel Amman" },
    { code: "SHER", name: "Sheraton Amman Al Nabil Hotel" },
    { code: "FAIR", name: "Fairmont Amman" },
    
    // Beijing Hotels
    { code: "PENI", name: "Peninsula Beijing" },
    { code: "REGB", name: "Regent Beijing" },
    { code: "ROSB", name: "Rosewood Beijing" },
    
    // Tokyo Hotels
    { code: "ANDT", name: "Andaz Tokyo Toranomon Hills" },
    { code: "RIST", name: "The Ritz-Carlton, Tokyo" },
    { code: "CONT", name: "Conrad Tokyo" },
    
    // Sydney Hotels
    { code: "PARS", name: "Park Hyatt Sydney" },
    { code: "FORT", name: "Four Seasons Hotel Sydney" },
    { code: "SHAS", name: "Shangri-La Hotel, Sydney" }
];