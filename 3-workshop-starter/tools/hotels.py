from typing import Dict, Any, Optional
from datetime import datetime
import random

# Simulated hotel database
SAMPLE_HOTELS = {
    "kyoto": [
        {
            "id": "KYT001",
            "name": "The Ritz-Carlton Kyoto",
            "rating": 5,
            "lat": 35.0262,
            "lon": 135.7721,
            "amenities": ["spa", "pool", "restaurant", "bar"],
            "price_range": "luxury"
        },
        {
            "id": "KYT002", 
            "name": "Hotel Granvia Kyoto",
            "rating": 4,
            "lat": 34.9858,
            "lon": 135.7588,
            "amenities": ["restaurant", "bar", "fitness-center"],
            "price_range": "upscale"
        },
        {
            "id": "KYT003",
            "name": "Kyoto Tower Hotel",
            "rating": 3,
            "lat": 34.9875,
            "lon": 135.7593,
            "amenities": ["restaurant", "laundry"],
            "price_range": "moderate"
        }
    ]
}

def book_hotel(
    location: str,
    check_in: str,
    check_out: str,
    guests: int,
    hotel_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulated hotel booking using Amadeus-like API.
    
    Args:
        location: City name (only "kyoto" supported in demo)
        check_in: Check-in date (ISO format)
        check_out: Check-out date (ISO format)
        guests: Number of guests
        hotel_id: Optional specific hotel ID to book
    
    Returns:
        Booking confirmation with details
    """
    location = location.lower()
    if location not in SAMPLE_HOTELS:
        raise ValueError(f"No hotels found in {location}")
        
    # Parse dates
    try:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
        nights = (check_out_date - check_in_date).days
        
        if nights <= 0:
            raise ValueError("Check-out must be after check-in")
            
    except ValueError as e:
        raise ValueError(f"Invalid dates: {str(e)}")
        
    # Find available hotel
    hotels = SAMPLE_HOTELS[location]
    if hotel_id:
        hotel = next((h for h in hotels if h["id"] == hotel_id), None)
        if not hotel:
            raise ValueError(f"Hotel {hotel_id} not found")
    else:
        # Randomly select a hotel
        hotel = random.choice(hotels)
        
    # Generate booking
    booking_id = f"BK{random.randint(10000, 99999)}"
    
    # Calculate simulated price
    base_price = {
        "luxury": 500,
        "upscale": 250,
        "moderate": 150
    }.get(hotel["price_range"], 200)
    
    total_price = base_price * nights * (1 + (guests-1)*0.5)  # 50% extra per additional guest
    
    return {
        "booking_id": booking_id,
        "hotel": hotel,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "nights": nights,
        "total_price": round(total_price, 2),
        "currency": "USD",
        "status": "confirmed",
        "confirmation_code": f"HTL{random.randint(100000, 999999)}",
        "cancellation_policy": "Free cancellation until 24 hours before check-in"
    }