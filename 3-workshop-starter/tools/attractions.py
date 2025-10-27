from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

# Simulated POI database
SAMPLE_ATTRACTIONS = {
    "kyoto": [
        {
            "name": "Kinkaku-ji (Golden Pavilion)",
            "type": "temple",
            "rating": 4.8,
            "lat": 35.0394,
            "lon": 135.7292,
            "description": "Famous Zen temple covered in gold leaf",
            "visit_duration": 2  # hours
        },
        {
            "name": "Fushimi Inari Shrine",
            "type": "shrine",
            "rating": 4.7,
            "lat": 34.9671,
            "lon": 135.7726,
            "description": "Famous for thousands of vermillion torii gates",
            "visit_duration": 3
        },
        {
            "name": "Arashiyama Bamboo Grove",
            "type": "nature",
            "rating": 4.6,
            "lat": 35.0170,
            "lon": 135.6711,
            "description": "Iconic bamboo forest pathway",
            "visit_duration": 1.5
        },
        {
            "name": "Nishiki Market",
            "type": "market",
            "rating": 4.5,
            "lat": 35.0048,
            "lon": 135.7639,
            "description": "Historic market street with food vendors",
            "visit_duration": 2
        },
        {
            "name": "Gion District",
            "type": "district",
            "rating": 4.7,
            "lat": 35.0039,
            "lon": 135.7761,
            "description": "Historic geisha district with traditional architecture",
            "visit_duration": 3
        }
    ]
}

def search_attractions(location: str, radius_km: float, top_n: int) -> List[Dict[str, Any]]:
    """
    Simulated attraction search using OpenTripMap-like API.
    
    Args:
        location: City name (only "kyoto" supported in demo)
        radius_km: Search radius in kilometers
        top_n: Number of results to return
    
    Returns:
        List of attractions with details
    """
    location = location.lower()
    if location not in SAMPLE_ATTRACTIONS:
        return []
    
    # Simulate some randomness in results
    attractions = SAMPLE_ATTRACTIONS[location].copy()
    random.shuffle(attractions)
    
    # Filter by radius (simplified)
    results = attractions[:min(top_n, len(attractions))]
    
    # Add simulated visit times
    now = datetime.now()
    for attraction in results:
        # Add random crowd levels for next few days
        crowd_forecast = []
        for i in range(7):
            date = now + timedelta(days=i)
            crowd_forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "crowd_level": random.choice(["low", "medium", "high"]),
                "best_time": random.choice(["morning", "afternoon", "evening"])
            })
        attraction["crowd_forecast"] = crowd_forecast
    
    return results