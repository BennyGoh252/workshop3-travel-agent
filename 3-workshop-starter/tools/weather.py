from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

def get_weather(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Simulated weather forecast using Open-Meteo-like API.
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date (ISO format: YYYY-MM-DD)
        end_date: End date (ISO format: YYYY-MM-DD)
    
    Returns:
        Dict with daily weather forecasts
    """
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days = (end - start).days + 1
    
    # Generate simulated forecasts
    daily = []
    for i in range(days):
        date = start + timedelta(days=i)
        
        # Simulate seasonal weather for Kyoto
        if date.month in [6, 7, 8]:  # Summer
            temp_high = random.uniform(28, 35)
            temp_low = random.uniform(20, 25)
            precip_prob = random.uniform(0.3, 0.7)  # Rainy season
        elif date.month in [12, 1, 2]:  # Winter
            temp_high = random.uniform(8, 15)
            temp_low = random.uniform(1, 7)
            precip_prob = random.uniform(0.2, 0.4)
        else:  # Spring/Fall
            temp_high = random.uniform(18, 25)
            temp_low = random.uniform(10, 17)
            precip_prob = random.uniform(0.1, 0.3)
            
        daily.append({
            "date": date.strftime("%Y-%m-%d"),
            "temperature_max": round(temp_high, 1),
            "temperature_min": round(temp_low, 1),
            "precipitation_probability": round(precip_prob, 2),
            "weather_code": random.choice([
                "clear",
                "partly_cloudy",
                "cloudy",
                "rain",
                "heavy_rain"
            ])
        })
    
    return {
        "latitude": lat,
        "longitude": lon,
        "daily": daily
    }