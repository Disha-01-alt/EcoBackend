import os
import logging
import json
import requests
import pandas as pd
import csv
from flask import Blueprint, jsonify, request
from utils.api_helpers import fetch_with_cache
from utils.data_processing import process_aqi_data, process_bird_data, process_pollution_data
from scrapers.nasa_scraper import get_deforestation_data
from scrapers.news_scraper import get_environmental_news

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Bird visualization data
birds_data = None
bird_families = None

def load_bird_visualization_data():
    global birds_data, bird_families
    try:
        # Read CSV with proper comma separation and header handling
        df = pd.read_csv('data/species-filter-results.csv', sep=',', quotechar='"')
        
        # Clean column names (remove spaces, make lowercase)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Verify we have the expected columns
        required_columns = {
            'family': 'family',
            'common_name': 'common_name', 
            'scientific_name': 'scientific_name',
            'population_size': 'population_size_(mature_individuals)',
            'population_trend': 'current_population_trend'
        }
        
        # Check if columns exist with flexible naming
        for standard_name, expected_name in required_columns.items():
            if expected_name not in df.columns:
                available = [col for col in df.columns if standard_name in col]
                if available:
                    required_columns[standard_name] = available[0]
                else:
                    logger.error(f"Missing required column: {standard_name}. Available columns: {df.columns.tolist()}")
                    return False
        
        # Standardize column names
        df = df.rename(columns={
            required_columns['family']: 'family',
            required_columns['common_name']: 'common_name',
            required_columns['scientific_name']: 'scientific_name',
            required_columns['population_size']: 'population_size',
            required_columns['population_trend']: 'population_trend'
        })
        
        # Clean data
        df = df.fillna('Unknown')
        df['population_size'] = df['population_size'].replace('Unknown', 'Unknown')
        
        # Convert to dictionary
        birds_data = df.to_dict('records')
        bird_families = df.groupby('family').apply(lambda x: x.to_dict('records')).to_dict()
        
        logger.info(f"Successfully loaded {len(birds_data)} bird species data")
        return True
    except Exception as e:
        logger.error(f"Error loading bird visualization data: {str(e)}")
        return False

# Load bird data on startup
load_bird_visualization_data()

# API keys
AQICN_API_KEY = os.environ.get("AQICN_API_KEY", "demo-key")
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY", "demo-key")
WORLD_BANK_API_KEY = os.environ.get("WORLD_BANK_API_KEY", "demo-key")
OPENAQ_API_KEY = os.environ.get("OPENAQ_API_KEY", "demo-key")

# AQI data endpoint - supports city name or coordinates
@api_bp.route('/aqi', methods=['GET'])
def get_aqi_data():
    # Check if we have coordinates or city
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    city = request.args.get('city', 'beijing')
    
    try:
        if lat and lng:
            # If we have coordinates, use geo endpoint
            url = f"https://api.waqi.info/feed/geo:{lat};{lng}/?token={AQICN_API_KEY}"
        else:
            # Otherwise use city name
            url = f"https://api.waqi.info/feed/{city}/?token={AQICN_API_KEY}"
        
        response = fetch_with_cache(url, cache_time=300)  # Cache for 5 minutes
        
        if response.status_code == 200:
            data = response.json()
            processed_data = process_aqi_data(data)
            return jsonify(processed_data)
        else:
            logger.error(f"Error fetching AQI data: {response.status_code}")
            return jsonify({"error": "Could not fetch AQI data", "status": response.status_code}), 500
    
    except Exception as e:
        logger.error(f"Exception in get_aqi_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Deforestation data endpoint
# @api_bp.route('/deforestation', methods=['GET'])
# def deforestation_data():
#     try:
#         data = get_deforestation_data()
#         return jsonify(data)
#     except Exception as e:
#         logger.error(f"Exception in deforestation_data: {str(e)}")
#         return jsonify({"error": str(e)}), 500


@api_bp.route("/deforestation", methods=["GET"])
def get_deforestation_data():
    data = []
    try:
        # Correct path to CSV
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'deforestation_data.csv')
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append({
                    "Country": row["Country"],
                    "Year": row["Year"],
                    "ForestArea": row["Forest Area (%)"]
                })
        

        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": "Failed to load deforestation data", "details": str(e)}), 500



# Environmental news endpoint
@api_bp.route('/news', methods=['GET'])
def environmental_news():
    try:
        news = get_environmental_news()
        return jsonify(news)
    except Exception as e:
        logger.error(f"Exception in environmental_news: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Bird data endpoint
@api_bp.route('/birds', methods=['GET'])
def bird_data():
    region = request.args.get('region', 'US-NY-063')  # Default to New York Cit
    
    try:
        url = f"https://api.ebird.org/v2/data/obs/{region}/recent"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        response = fetch_with_cache(url, headers=headers, cache_time=3600)  # Cache for 1 hour
        
        if response.status_code == 200:
            data = response.json()
            processed_data = process_bird_data(data)
            return jsonify(processed_data)
        else:
            logger.error(f"Error fetching bird data: {response.status_code}")
            return jsonify({"error": "Could not fetch bird data", "status": response.status_code}), 500
    
    except Exception as e:
        logger.error(f"Exception in bird_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Hotspot data for birds
@api_bp.route('/birds/hotspots', methods=['GET'])
def bird_hotspots():
    lat = request.args.get('lat', '40.7128')  # Default to NYC
    lng = request.args.get('lng', '-74.0060')
    
    try:
        url = f"https://api.ebird.org/v2/ref/hotspot/geo?lat={lat}&lng={lng}&fmt=json"
        headers = {"X-eBirdApiToken": EBIRD_API_KEY}
        response = fetch_with_cache(url, headers=headers, cache_time=86400)  # Cache for 24 hours
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"Error fetching bird hotspots: {response.status_code}")
            return jsonify({"error": "Could not fetch bird hotspots", "status": response.status_code}), 500
    
    except Exception as e:
        logger.error(f"Exception in bird_hotspots: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Pollution rates endpoint
@api_bp.route('/pollution', methods=['GET','POST'])
def pollution_rates():
    country = request.args.get('country', 'USA')
    
    try:
        # Using OpenAQ for air pollution data
        openaq_url = f"https://api.openaq.org/v2/latest?limit=100&page=1&offset=0&sort=desc&country={country}&order_by=lastUpdated"
        headers = {}
        if OPENAQ_API_KEY:
            headers["X-API-Key"] = OPENAQ_API_KEY
        
        response = fetch_with_cache(openaq_url, headers=headers, cache_time=3600)  # Cache for 1 hour
        
        if response.status_code == 200:
            data = response.json()
            processed_data = process_pollution_data(data)
            return jsonify(processed_data)
        else:
            logger.error(f"Error fetching pollution data: {response.status_code}")
            return redirect("https://radiant-tapioca-6b0438.netlify.app/")
    
    except Exception as e:
        logger.error(f"Exception in pollution_rates: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Enhanced Impact calculation endpoint
@api_bp.route('/calculate-impact', methods=['GET','POST'])
#def calculate_impact():
#    try:
#        data = request.get_json()
#        if not data:
#            return jsonify({"error": "No data provided"}), 400
#            
#        # Calculate impact using the provided data
#        result = {
#            "carbon_footprint": 0,
#            "water_footprint": 0,
#            "land_footprint": 0,
#            "breakdown": {},
#            "recommendations": []
#        }
#        
#        return jsonify(result)
#    except Exception as e:
#        logger.error(f"Exception in calculate_impact: {str(e)}")
#        return jsonify({"error": str(e)}), 500
def calculate_impact():
    try:
        data = request.json
        
        # Get transportation inputs
        transport_type = data.get('transportation_type', 'car')
        commute_distance = float(data.get('commute_distance', 20))  # km per day
        flights_per_year = int(data.get('flights_per_year', 2))
        
        # Get home energy inputs
        home_size = float(data.get('home_size', 100))  # sq meters
        household_members = int(data.get('household_members', 2))
        energy_source = data.get('energy_source', 'grid')
        
        # Get diet inputs
        diet_type = data.get('diet_type', 'meat_medium')
        local_food_percent = float(data.get('local_food_percent', 30))  # percent
        
        # Get waste inputs
        recycling_rate = float(data.get('recycling_rate', 50))  # percent
        shopping_frequency = data.get('shopping_frequency', 'moderate')
        
        # Calculate carbon footprint components
        
        # Transportation impact calculation
        transport_factors = {
            'car': 0.192,  # kg CO2 per km
            'electric_car': 0.053,  # kg CO2 per km (depends on grid)
            'public_transport': 0.058,  # kg CO2 per km
            'carpool': 0.096,  # kg CO2 per km (half of car)
            'bicycle': 0.0,  # kg CO2 per km
            'walking': 0.0   # kg CO2 per km
        }
        
        transportation_impact = commute_distance * 365 * transport_factors.get(transport_type, 0.192)
        flight_impact = flights_per_year * 1100  # kg CO2 per round-trip flight (average)
        
        # Home energy impact calculation
        energy_factors = {
            'grid': 0.3,  # kg CO2 per sq meter per day
            'renewable': 0.02,  # kg CO2 per sq meter per day
            'natural_gas': 0.2,  # kg CO2 per sq meter per day
            'oil': 0.35,  # kg CO2 per sq meter per day
            'mixed': 0.25  # kg CO2 per sq meter per day
        }
        
        # Adjust for household size
        home_energy_impact = (home_size * 365 * energy_factors.get(energy_source, 0.3)) / max(1, household_members)
        
        # Diet impact calculation
        diet_factors = {
            'meat_heavy': 7.9,  # kg CO2 per day
            'meat_medium': 5.1,  # kg CO2 per day
            'pescatarian': 3.9,  # kg CO2 per day
            'vegetarian': 3.3,  # kg CO2 per day
            'vegan': 2.5   # kg CO2 per day
        }
        
        # Adjust for local food consumption (local reduces by up to 25%)
        local_food_adjustment = 1 - (local_food_percent * 0.0025)  # Each % reduces impact by 0.25%
        diet_impact = 365 * diet_factors.get(diet_type, 5.1) * local_food_adjustment
        
        # Waste impact calculation
        waste_base = 1100  # kg CO2 per year baseline
        
        # Recycling reduces waste impact
        recycling_adjustment = 1 - (recycling_rate * 0.005)  # Each % reduces impact by 0.5%
        
        # Shopping frequency impact
        shopping_factors = {
            'minimal': 0.5,
            'moderate': 1.0,
            'frequent': 1.5,
            'very_frequent': 2.0
        }
        
        waste_impact = waste_base * recycling_adjustment * shopping_factors.get(shopping_frequency, 1.0)
        
        # Calculate total carbon footprint (kg CO2 per year)
        carbon_footprint = transportation_impact + flight_impact + home_energy_impact + diet_impact + waste_impact
        
        # Convert to metric tons
        carbon_footprint_tons = carbon_footprint / 1000
        
        # Calculate water footprint (liters per day)
        water_base = 150  # direct usage (showering, drinking, etc.)
        
        # Diet adds significant water usage
        diet_water = {
            'meat_heavy': 5000,
            'meat_medium': 3800,
            'pescatarian': 2800,
            'vegetarian': 2200,
            'vegan': 1700
        }
        
        water_footprint = water_base + diet_water.get(diet_type, 3800)
        
        # Calculate land footprint (global hectares)
        land_base = 0.2  # housing and infrastructure
        
        diet_land = {
            'meat_heavy': 2.0,
            'meat_medium': 1.2,
            'pescatarian': 0.8,
            'vegetarian': 0.6,
            'vegan': 0.4
        }
        
        land_footprint = land_base + diet_land.get(diet_type, 1.2)
        
        # Breakdown of carbon footprint by category
        breakdown = {
            'transportation': round(transportation_impact / 1000, 2),
            'flights': round(flight_impact / 1000, 2),
            'home_energy': round(home_energy_impact / 1000, 2),
            'diet': round(diet_impact / 1000, 2),
            'waste': round(waste_impact / 1000, 2)
        }
        
        # Generate personalized recommendations
        recommendations = []
        
        # Transportation recommendations
        if transport_type in ['car', 'electric_car']:
            recommendations.append({
                'category': 'transport',
                'impact': 'high',
                'title': 'Consider public transit or carpooling',
                'description': 'Taking public transportation or sharing rides can reduce your carbon footprint significantly.'
            })
        
        # Flight recommendations
        if flights_per_year > 3:
            recommendations.append({
                'category': 'transport',
                'impact': 'high',
                'title': 'Reduce air travel',
                'description': 'Consider fewer flights or alternatives like train travel for shorter distances.'
            })
        
        # Energy recommendations
        if energy_source != 'renewable':
            recommendations.append({
                'category': 'energy',
                'impact': 'high',
                'title': 'Switch to renewable energy',
                'description': 'Consider solar panels or a renewable energy provider for your home electricity.'
            })
        
        # Diet recommendations
        if diet_type in ['meat_heavy', 'meat_medium']:
            recommendations.append({
                'category': 'diet',
                'impact': 'high',
                'title': 'Reduce meat consumption',
                'description': 'Try incorporating more plant-based meals into your diet to reduce your environmental impact.'
            })
        
        # Local food recommendations
        if local_food_percent < 40:
            recommendations.append({
                'category': 'diet',
                'impact': 'medium',
                'title': 'Choose local and seasonal foods',
                'description': 'Buying locally produced food reduces transportation emissions and supports local farmers.'
            })
        
        # Recycling recommendations
        if recycling_rate < 60:
            recommendations.append({
                'category': 'waste',
                'impact': 'medium',
                'title': 'Increase recycling efforts',
                'description': 'Try to recycle more of your waste and compost food scraps if possible.'
            })
        
        # Shopping recommendations
        if shopping_frequency in ['frequent', 'very_frequent']:
            recommendations.append({
                'category': 'waste',
                'impact': 'medium',
                'title': 'Reduce consumption',
                'description': 'Consider buying fewer items and focusing on quality, durable products that last longer.'
            })
        
        result = {
            "carbon_footprint": round(carbon_footprint_tons, 2),  # tons CO2 per year
            "water_footprint": round(water_footprint, 0),  # liters per day
            "land_footprint": round(land_footprint, 2),  # global hectares
            "breakdown": breakdown,
            "recommendations": recommendations
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Exception in calculate_impact: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Bird Visualization API Endpoints

# Get all bird species
@api_bp.route('/birds/all', methods=['GET'])
def get_all_birds():
    try:
        if not birds_data:
            if not load_bird_visualization_data():
                return jsonify({"error": "Failed to load bird data"}), 500
        
        # Return only essential data for autocomplete to reduce payload size
        simplified_birds = []
        for bird in birds_data:
            simplified_birds.append({
                "common_name": bird.get("common_name", "Unknown"),
                "scientific_name": bird.get("scientific_name", "Unknown"),
                "family": bird.get("family", "Unknown")
            })
        
        return jsonify(simplified_birds)
        
    except Exception as e:
        logger.error(f"Exception in get_all_birds: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get bird by common name
@api_bp.route('/bird/<common_name>', methods=['GET'])
def get_bird(common_name):
    try:
        if not birds_data:
            if not load_bird_visualization_data():
                return jsonify({"error": "Failed to load bird data"}), 500
        
        # Find bird by common name (case insensitive)
        bird = next((b for b in birds_data if b['common_name'].lower() == common_name.lower()), None)
        
        if not bird:
            return jsonify({"error": "Bird not found"}), 404
        
        # Get all birds in the same family
        family = bird['family']
        family_birds = bird_families.get(family, [])
        
        # Limit family birds to 50 to avoid payload being too large
        family_birds = family_birds[:50]
        
        # Calculate trend statistics for family
        trends = {}
        for b in family_birds:
            trend = b.get('population_trend', 'Unknown')
            if trend not in trends:
                trends[trend] = 0
            trends[trend] += 1
        
        # Calculate population size statistics for family (only for first 10 birds)
        population_sizes = {}
        for b in family_birds[:10]:
            size = b.get('population_size', 'Unknown')
            if size != 'Unknown' and str(size).isdigit():
                population_sizes[b['common_name']] = int(size)
        
        result = {
            "bird": bird,
            "family": family_birds,
            "family_stats": {
                "trends": trends,
                "population_sizes": population_sizes
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Exception in get_bird: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Search birds by name
@api_bp.route('/birds/search', methods=['GET'])
def search_birds():
    try:
        if not birds_data:
            if not load_bird_visualization_data():
                return jsonify({"error": "Failed to load bird data"}), 500
        
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify([])
        
        # Search birds by name (case insensitive)
        results = [b for b in birds_data if query in b['common_name'].lower()]
        
        # Limit results
        limit = int(request.args.get('limit', 10))
        results = results[:limit]
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Exception in search_birds: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get birds by family
@api_bp.route('/birds/family/<family_name>', methods=['GET'])
def get_family_birds(family_name):
    try:
        if not bird_families:
            if not load_bird_visualization_data():
                return jsonify({"error": "Failed to load bird data"}), 500
        
        # Find family (case insensitive)
        family = None
        for f in bird_families:
            if f.lower() == family_name.lower():
                family = f
                break
        
        if not family:
            return jsonify({"error": "Family not found"}), 404
        
        return jsonify(bird_families[family])
        
    except Exception as e:
        logger.error(f"Exception in get_family_birds: {str(e)}")
        return jsonify({"error": str(e)}), 500
