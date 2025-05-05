import requests
import time
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Simple in-memory cache
cache = {}

def fetch_with_cache(url: str, headers: Optional[Dict[str, str]] = None, 
                     cache_time: int = 300) -> requests.Response:
    """
    Fetch data from URL with caching
    
    Args:
        url: URL to fetch
        headers: Optional request headers
        cache_time: Cache time in seconds (default: 5 minutes)
        
    Returns:
        Response object
    """
    cache_key = f"{url}_{str(headers)}"
    
    # Check if we have a cached response
    if cache_key in cache:
        cached_time, cached_response = cache[cache_key]
        # If the cache is still valid, return cached response
        if time.time() - cached_time < cache_time:
            logger.debug(f"Returning cached response for {url}")
            return cached_response
    
    # Make the request
    logger.info(f"Fetching fresh data from {url}")
    response = requests.get(url, headers=headers)
    
    # Cache the response
    if response.status_code == 200:
        cache[cache_key] = (time.time(), response)
    
    return response

def safe_api_request(url: str, headers: Optional[Dict[str, str]] = None, 
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Makes a safe API request with error handling
    
    Args:
        url: API endpoint URL
        headers: Optional request headers
        params: Optional query parameters
        
    Returns:
        Parsed JSON response or error dictionary
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
        return {"error": f"Connection error occurred: {conn_err}"}
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        return {"error": f"Timeout error occurred: {timeout_err}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Error occurred: {req_err}")
        return {"error": f"Error occurred: {req_err}"}
    except ValueError as json_err:
        logger.error(f"JSON parsing error: {json_err}")
        return {"error": f"JSON parsing error: {json_err}"}
