#!/usr/bin/env python3
"""
Process hotel CSV file and generate enhanced hotel autocomplete data
"""
import csv
import json
import re

def clean_hotel_name(name):
    """Clean and normalize hotel name"""
    if not name:
        return ""
    # Remove extra spaces and normalize
    name = re.sub(r'\s+', ' ', name.strip())
    return name

def extract_city(city_field):
    """Extract clean city name from city field"""
    if not city_field:
        return ""
    # Clean up city name
    city = city_field.strip()
    # Remove common suffixes like "/Antalya" 
    city = re.sub(r'/.*$', '', city)
    return city

def generate_hotel_code(hotel_name, city):
    """Generate a unique hotel code from name and city"""
    # Take first 4 letters of hotel name and first 2 of city
    name_part = re.sub(r'[^A-Za-z]', '', hotel_name)[:4].upper()
    city_part = re.sub(r'[^A-Za-z]', '', city)[:2].upper()
    return f"{name_part}{city_part}"

def process_csv_file(csv_path):
    """Process the CSV file and extract hotel data"""
    hotels = []
    cities = set()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            hotel_name = clean_hotel_name(row.get('Hotel Name', ''))
            city = extract_city(row.get('City', ''))
            
            if hotel_name and city:
                hotel_code = generate_hotel_code(hotel_name, city)
                
                hotels.append({
                    'code': hotel_code,
                    'name': hotel_name,
                    'city': city
                })
                
                cities.add(city)
    
    # Sort hotels by name for better organization
    hotels.sort(key=lambda x: x['name'])
    
    # Convert cities set to sorted list with codes
    city_list = []
    for city in sorted(cities):
        city_code = re.sub(r'[^A-Za-z]', '', city)[:3].upper()
        city_list.append({
            'code': city_code,
            'name': f"{city}, Turkey"
        })
    
    return hotels, city_list

def generate_js_output(hotels, cities):
    """Generate JavaScript code for the hotel data"""
    
    # Generate hotel names array
    hotel_js = "const HOTEL_NAMES = [\n"
    for hotel in hotels:
        hotel_js += f'    {{ code: "{hotel["code"]}", name: "{hotel["name"]}" }},\n'
    hotel_js += "];\n\n"
    
    # Generate additional cities
    cities_js = "// Additional Turkish cities from hotel data\n"
    cities_js += "const ADDITIONAL_HOTEL_CITIES = [\n"
    for city in cities:
        cities_js += f'    {{ code: "{city["code"]}", name: "{city["name"]}" }},\n'
    cities_js += "];\n\n"
    
    return hotel_js + cities_js

def main():
    """Main processing function"""
    csv_path = "attached_assets/hotelconswithaddress_1751201464690.csv"
    
    print("Processing hotel CSV file...")
    hotels, cities = process_csv_file(csv_path)
    
    print(f"Processed {len(hotels)} hotels from {len(cities)} cities")
    
    # Generate JavaScript output
    js_output = generate_js_output(hotels, cities)
    
    # Write to output file
    with open("hotel_data_turkish.js", "w", encoding="utf-8") as f:
        f.write(js_output)
    
    print("Generated hotel_data_turkish.js")
    print("\nSample hotels:")
    for i, hotel in enumerate(hotels[:10]):
        print(f"  {hotel['name']} - {hotel['city']}")
    
    if len(hotels) > 10:
        print(f"  ... and {len(hotels) - 10} more hotels")

if __name__ == "__main__":
    main()