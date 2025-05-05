import logging
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Cache for deforestation data
deforestation_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 86400  # 24 hours
}

def get_deforestation_data() -> Dict[str, Any]:
    """
    Scrape deforestation data from NASA Earth Observatory
    
    Returns:
        Dictionary with deforestation data
    """
    # Check cache first
    if (deforestation_cache['data'] is not None and 
        time.time() - deforestation_cache['timestamp'] < deforestation_cache['cache_duration']):
        logger.info("Returning cached deforestation data")
        return deforestation_cache['data']
    
    try:
        # NASA Earth Observatory Global Maps site for forest cover
        url = "https://earthobservatory.nasa.gov/global-maps/MOD_NDVI_M"
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract recent articles about deforestation
        articles = []
        article_elements = soup.select('.list-recent-posts .article')
        
        for article in article_elements[:5]:  # Get up to 5 recent articles
            title_element = article.select_one('.article-title a')
            date_element = article.select_one('.article-date')
            summary_element = article.select_one('.article-excerpt p')
            image_element = article.select_one('img')
            
            if title_element and date_element:
                title = title_element.text.strip()
                link = title_element['href'] if 'href' in title_element.attrs else ""
                date = date_element.text.strip()
                
                # Only include articles related to forests/deforestation
                if any(keyword in title.lower() for keyword in ['forest', 'deforest', 'tree', 'amazon', 'rainforest']):
                    articles.append({
                        'title': title,
                        'date': date,
                        'link': f"https://earthobservatory.nasa.gov{link}" if link.startswith('/') else link,
                        'summary': summary_element.text.strip() if summary_element else "",
                        'image': image_element['src'] if image_element and 'src' in image_element.attrs else ""
                    })
        
        # Try to get forest data from Global Forest Watch
        gfw_data = get_gfw_data()
        
        # Combine data
        result = {
            'timestamp': datetime.now().isoformat(),
            'articles': articles,
            'forest_data': gfw_data if gfw_data else {},
            'source': 'NASA Earth Observatory and Global Forest Watch'
        }
        
        # Cache the result
        deforestation_cache['data'] = result
        deforestation_cache['timestamp'] = time.time()
        
        return result
    
    except Exception as e:
        logger.error(f"Error scraping deforestation data: {str(e)}")
        # If we have cached data, return it even if expired
        if deforestation_cache['data'] is not None:
            return deforestation_cache['data']
        return {
            'error': f"Failed to scrape deforestation data: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def get_gfw_data() -> Optional[Dict[str, Any]]:
    """
    Get forest data from Global Forest Watch API
    
    Returns:
        Dictionary with forest loss data or None on failure
    """
    try:
        # Global Forest Watch summary data
        url = "https://gfw-api.org/forest-change/summary-stats/v1/loss"
        params = {
            'period': '2001-01-01,2022-12-31',
            'gladConfirmOnly': False,
            'aggregate_values': True
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {})
        else:
            logger.warning(f"Failed to get GFW data: {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Error getting GFW data: {str(e)}")
        return None

def get_deforestation_stats() -> Dict[str, Any]:
    """
    Generate some summary statistics based on available deforestation data
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        # Try to get real data first
        data = get_deforestation_data()
        
        forest_data = data.get('forest_data', {})
        
        # If we have real data, return it
        if forest_data and 'totalLoss' in forest_data:
            return {
                'total_loss': forest_data.get('totalLoss', 0),
                'total_gain': forest_data.get('totalGain', 0),
                'net_change': forest_data.get('totalLoss', 0) - forest_data.get('totalGain', 0),
                'years': forest_data.get('years', []),
                'source': 'Global Forest Watch'
            }
        
        # Otherwise synthesize the best statistics we can with references
        # Using Global Forest Watch reported numbers
        # These are static references to published data
        return {
            'total_loss_ha': 411000000,  # Approximate global forest loss 2001-2021 in hectares
            'annual_loss_ha': 25600000,  # Approximate annual loss in hectares
            'primary_forest_loss_2021': 3750000,  # Hectares of primary forest loss in 2021
            'reference': 'Reference: Global Forest Watch reports approximately 411 million hectares of tree cover loss globally from 2001 to 2021',
            'source': 'Global Forest Watch (Static Reference)',
            'disclaimer': 'These are static reference values. For real-time data, please refer to globalforestwatch.org'
        }
    
    except Exception as e:
        logger.error(f"Error generating deforestation stats: {str(e)}")
        return {
            'error': f"Failed to generate deforestation statistics: {str(e)}",
            'source': 'Error'
        }
