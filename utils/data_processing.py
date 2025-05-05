import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def process_aqi_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process AQI data from AQICN API
    
    Args:
        data: Raw API response
        
    Returns:
        Processed AQI data
    """
    try:
        if data.get('status') != 'ok':
            logger.warning(f"API returned non-OK status: {data.get('status')}")
            return {
                "error": "API returned non-OK status",
                "raw_status": data.get('status')
            }
        
        result = data.get('data', {})
        
        # Check if we have a valid AQI value
        aqi = result.get('aqi')
        if aqi is None:
            return {
                "error": "No AQI data available for this location",
                "raw_data": result
            }
        
        # For city data, handle both direct name and complex object
        city = result.get('city')
        city_name = "Unknown"
        if isinstance(city, dict):
            city_name = city.get('name', 'Unknown')
        elif isinstance(city, str):
            city_name = city
        
        # Extract time info and convert to ISO format
        time_data = result.get('time', {})
        if isinstance(time_data, dict):
            time_str = time_data.get('s', '')
            time_iso = time_data.get('iso', '')
        else:
            time_str = str(time_data)
            time_iso = str(time_data)
        
        # Build processed data structure
        processed = {
            "city": {
                "name": city_name
            },
            "aqi": aqi,
            "time": {
                "s": time_str,
                "iso": time_iso
            },
            "dominantPollutant": result.get('dominentpol', 'Unknown'),
            "iaqi": {}  # Individual Air Quality Index
        }
        
        # Add location data if available
        if 'geo' in result and isinstance(result['geo'], list) and len(result['geo']) >= 2:
            processed["geo"] = {
                "lat": result['geo'][0],
                "lng": result['geo'][1]
            }
        
        # Process individual pollutants
        iaqi = result.get('iaqi', {})
        for pollutant, value in iaqi.items():
            if isinstance(value, dict) and 'v' in value:
                processed["iaqi"][pollutant] = value
            elif isinstance(value, (int, float)):
                processed["iaqi"][pollutant] = {"v": value}
        
        # Add forecast if available
        if 'forecast' in result and isinstance(result['forecast'], dict):
            processed["forecast"] = result['forecast']
        
        # Add AQI category
        aqi_value = processed["aqi"]
        if aqi_value <= 50:
            processed["category"] = "Good"
            processed["color"] = "#00e400"
        elif aqi_value <= 100:
            processed["category"] = "Moderate"
            processed["color"] = "#ffff00"
        elif aqi_value <= 150:
            processed["category"] = "Unhealthy for Sensitive Groups"
            processed["color"] = "#ff7e00"
        elif aqi_value <= 200:
            processed["category"] = "Unhealthy"
            processed["color"] = "#ff0000"
        elif aqi_value <= 300:
            processed["category"] = "Very Unhealthy"
            processed["color"] = "#99004c"
        else:
            processed["category"] = "Hazardous"
            processed["color"] = "#7e0023"
        
        return processed
    
    except Exception as e:
        logger.error(f"Error processing AQI data: {str(e)}")
        return {"error": f"Error processing data: {str(e)}"}

def process_bird_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process bird data from eBird API
    
    Args:
        data: Raw API response
        
    Returns:
        Processed bird data
    """
    try:
        if not data:
            return {"birds": [], "counts": {}, "total": 0}
        
        # Species count
        species_count = {}
        for sighting in data:
            species = sighting.get('comName', 'Unknown')
            if species in species_count:
                species_count[species] += 1
            else:
                species_count[species] = 1
        
        # Sort species by observation count
        sorted_species = sorted(species_count.items(), key=lambda x: x[1], reverse=True)
        top_species = dict(sorted_species[:10])  # Top 10 species
        
        # Process bird sightings with location data
        processed_birds = []
        for sighting in data:
            processed_birds.append({
                "species": sighting.get('comName', 'Unknown'),
                "scientific_name": sighting.get('sciName', 'Unknown'),
                "location": sighting.get('locName', 'Unknown'),
                "observation_date": sighting.get('obsDt', 'Unknown'),
                "count": sighting.get('howMany', 1),
                "coordinates": {
                    "lat": sighting.get('lat', 0),
                    "lng": sighting.get('lng', 0)
                }
            })
        
        return {
            "birds": processed_birds,
            "counts": top_species,
            "total": len(data)
        }
    
    except Exception as e:
        logger.error(f"Error processing bird data: {str(e)}")
        return {"error": f"Error processing data: {str(e)}"}

def process_pollution_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process pollution data from OpenAQ API
    
    Args:
        data: Raw API response
        
    Returns:
        Processed pollution data
    """
    try:
        results = data.get('results', [])
        if not results:
            return {"locations": [], "pollutants": {}, "total": 0}
        
        # Process pollution data by location and pollutant type
        locations = []
        pollutant_counts = {}
        pollutant_values = {}
        
        for location in results:
            loc_name = location.get('location', 'Unknown')
            measurements = location.get('measurements', [])
            
            loc_data = {
                "name": loc_name,
                "city": location.get('city', 'Unknown'),
                "coordinates": {
                    "latitude": location.get('coordinates', {}).get('latitude', 0),
                    "longitude": location.get('coordinates', {}).get('longitude', 0)
                },
                "measurements": []
            }
            
            for measurement in measurements:
                parameter = measurement.get('parameter', 'Unknown')
                value = measurement.get('value', 0)
                unit = measurement.get('unit', '')
                
                # Count pollutant occurrences
                if parameter in pollutant_counts:
                    pollutant_counts[parameter] += 1
                    pollutant_values[parameter].append(value)
                else:
                    pollutant_counts[parameter] = 1
                    pollutant_values[parameter] = [value]
                
                loc_data["measurements"].append({
                    "parameter": parameter,
                    "value": value,
                    "unit": unit,
                    "lastUpdated": measurement.get('lastUpdated', 'Unknown')
                })
            
            locations.append(loc_data)
        
        # Calculate average values for each pollutant
        pollutant_avg = {}
        for parameter, values in pollutant_values.items():
            pollutant_avg[parameter] = sum(values) / len(values) if values else 0
        
        return {
            "locations": locations,
            "pollutants": {
                "counts": pollutant_counts,
                "averages": pollutant_avg
            },
            "total": len(results)
        }
    
    except Exception as e:
        logger.error(f"Error processing pollution data: {str(e)}")
        return {"error": f"Error processing data: {str(e)}"}
