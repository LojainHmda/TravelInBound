/**
 * Static airline and airport data for autocomplete functionality
 * This provides offline data that doesn't require API calls
 */
const AIRLINE_DATA = [
    { code: "AA", name: "American Airlines" },
    { code: "AF", name: "Air France" },
    { code: "BA", name: "British Airways" },
    { code: "DL", name: "Delta Air Lines" },
    { code: "EK", name: "Emirates" },
    { code: "EY", name: "Etihad Airways" },
    { code: "JL", name: "Japan Airlines" },
    { code: "KL", name: "KLM Royal Dutch Airlines" },
    { code: "LH", name: "Lufthansa" },
    { code: "MS", name: "EgyptAir" },
    { code: "QF", name: "Qantas" },
    { code: "QR", name: "Qatar Airways" },
    { code: "RJ", name: "Royal Jordanian" },
    { code: "SQ", name: "Singapore Airlines" },
    { code: "TK", name: "Turkish Airlines" },
    { code: "UA", name: "United Airlines" }
];

const AIRPORT_DATA = [
    { code: "AMM", name: "Queen Alia International Airport (Amman, Jordan)" },
    { code: "AMS", name: "Amsterdam Airport Schiphol (Amsterdam, Netherlands)" },
    { code: "ATL", name: "Hartsfield-Jackson Atlanta International Airport (Atlanta, USA)" },
    { code: "BKK", name: "Suvarnabhumi Airport (Bangkok, Thailand)" },
    { code: "CAI", name: "Cairo International Airport (Cairo, Egypt)" },
    { code: "CDG", name: "Charles de Gaulle Airport (Paris, France)" },
    { code: "DFW", name: "Dallas/Fort Worth International Airport (Dallas, USA)" },
    { code: "DOH", name: "Hamad International Airport (Doha, Qatar)" },
    { code: "DXB", name: "Dubai International Airport (Dubai, UAE)" },
    { code: "FRA", name: "Frankfurt Airport (Frankfurt, Germany)" },
    { code: "HKG", name: "Hong Kong International Airport (Hong Kong)" },
    { code: "IST", name: "Istanbul Airport (Istanbul, Turkey)" },
    { code: "JFK", name: "John F. Kennedy International Airport (New York, USA)" },
    { code: "LHR", name: "London Heathrow Airport (London, UK)" },
    { code: "LAX", name: "Los Angeles International Airport (Los Angeles, USA)" },
    { code: "MAD", name: "Adolfo Suárez Madrid–Barajas Airport (Madrid, Spain)" },
    { code: "MEX", name: "Mexico City International Airport (Mexico City, Mexico)" },
    { code: "MUC", name: "Munich Airport (Munich, Germany)" },
    { code: "ORD", name: "O'Hare International Airport (Chicago, USA)" },
    { code: "SIN", name: "Singapore Changi Airport (Singapore)" },
    { code: "SVO", name: "Sheremetyevo International Airport (Moscow, Russia)" },
    { code: "SYD", name: "Sydney Airport (Sydney, Australia)" },
    { code: "YYZ", name: "Toronto Pearson International Airport (Toronto, Canada)" },
    { code: "ZRH", name: "Zurich Airport (Zurich, Switzerland)" }
];