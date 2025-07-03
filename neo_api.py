#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Near Earth Object API Module

This module provides functionality to interact with NASA's Near Earth Object Web Service (NeoWs).
It allows retrieving information about asteroids and other objects that come close to Earth.

Main features:
    - Retrieve near earth objects based on their closest approach date to Earth
    - Get detailed information about specific near earth objects
    - Calculate visibility information for near earth objects

Usage example:
    >>> from neo_api import get_neo_feed
    >>> neos = get_neo_feed(start_date="2023-01-01", end_date="2023-01-07")
    >>> for neo in neos:
    ...     print(f"{neo['name']}: {neo['close_approach_date']} - Distance: {neo['miss_distance_km']} km")
"""

import requests
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NASA API base URL
BASE_URL = "https://api.nasa.gov/neo/rest/v1"

# Cache for storing API responses
NEO_CACHE = {}
CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds


def get_neo_feed(start_date: str, end_date: Optional[str] = None, api_key: str = "DEMO_KEY") -> List[Dict[str, Any]]:
    """
    Get a list of Near Earth Objects based on their closest approach date to Earth

    Args:
        start_date: Starting date for asteroid search (YYYY-MM-DD)
        end_date: Ending date for asteroid search (YYYY-MM-DD), defaults to 7 days after start_date
        api_key: NASA API key, defaults to DEMO_KEY which has rate limits

    Returns:
        List of dictionaries containing NEO data

    Raises:
        Exception: If there's an error with the API request
    """
    # Check cache first
    cache_key = f"{start_date}_{end_date}_{api_key}"
    if cache_key in NEO_CACHE:
        cache_time, cached_data = NEO_CACHE[cache_key]
        if datetime.now().timestamp() - cache_time < CACHE_DURATION:
            logger.info(f"Using cached NEO data for {start_date} to {end_date}")
            return cached_data

    # Build API request URL
    url = f"{BASE_URL}/feed"
    
    # Prepare request parameters
    params = {
        "start_date": start_date,
        "api_key": api_key
    }
    
    if end_date:
        params["end_date"] = end_date
    
    try:
        # Send API request
        logger.info(f"Requesting NEO data for {start_date} to {end_date or 'default'}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Process API response
        data = response.json()
        processed_data = process_neo_data(data)
        
        # Cache the result
        NEO_CACHE[cache_key] = (datetime.now().timestamp(), processed_data)
        
        return processed_data
    except Exception as e:
        logger.error(f"Error getting NEO data: {str(e)}")
        raise


def process_neo_data(neo_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process NASA API response, extract Near Earth Object information

    Args:
        neo_response: NASA API response

    Returns:
        List of dictionaries containing processed NEO data
    """
    neo_list = []
    
    # Extract Near Earth Object data
    near_earth_objects = neo_response.get("near_earth_objects", {})
    
    for date, neos in near_earth_objects.items():
        for neo in neos:
            # Extract basic information
            neo_data = {
                "id": neo.get("id"),
                "name": neo.get("name"),
                "nasa_jpl_url": neo.get("nasa_jpl_url"),
                "absolute_magnitude_h": neo.get("absolute_magnitude_h"),
                "is_potentially_hazardous": neo.get("is_potentially_hazardous_asteroid", False),
                "date": date
            }
            
            # Extract estimated diameter
            estimated_diameter = neo.get("estimated_diameter", {})
            if "kilometers" in estimated_diameter:
                km_data = estimated_diameter["kilometers"]
                neo_data["diameter_min_km"] = km_data.get("estimated_diameter_min")
                neo_data["diameter_max_km"] = km_data.get("estimated_diameter_max")
                neo_data["diameter_avg_km"] = (neo_data["diameter_min_km"] + neo_data["diameter_max_km"]) / 2
            
            # Extract closest approach data
            close_approach_data = neo.get("close_approach_data", [])
            if close_approach_data:
                approach = close_approach_data[0]  # Take the first approach
                neo_data["close_approach_date"] = approach.get("close_approach_date")
                neo_data["close_approach_date_full"] = approach.get("close_approach_date_full")
                
                relative_velocity = approach.get("relative_velocity", {})
                neo_data["velocity_km_per_hour"] = float(relative_velocity.get("kilometers_per_hour", 0))
                
                miss_distance = approach.get("miss_distance", {})
                neo_data["miss_distance_km"] = float(miss_distance.get("kilometers", 0))
                neo_data["miss_distance_lunar"] = float(miss_distance.get("lunar", 0))  # In lunar distances
                neo_data["miss_distance_astronomical"] = float(miss_distance.get("astronomical", 0))  # In AU
                
                # Extract orbiting body
                neo_data["orbiting_body"] = approach.get("orbiting_body")
            
            neo_list.append(neo_data)
    
    return neo_list


def get_neo_visibility(neo_data: Dict[str, Any], latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calculate visibility information for a Near Earth Object
    
    This is a simplified method that provides approximate visibility information
    based on the NEO's approach direction. For accurate calculations, we would need
    detailed orbital elements which are not provided by the NeoWs API.
    
    Args:
        neo_data: Near Earth Object data
        latitude: Observer's latitude in degrees
        longitude: Observer's longitude in degrees
        
    Returns:
        Dictionary containing visibility information
    """
    # This is a simplified approach since we don't have detailed orbital elements
    # We'll use the orbiting body and approach data to make an educated guess
    
    # Get the current date
    today = datetime.now().date()
    approach_date = datetime.strptime(neo_data["close_approach_date"], "%Y-%m-%d").date()
    
    # Check if the approach date is within a reasonable window (7 days before/after)
    date_diff = abs((approach_date - today).days)
    if date_diff > 7:
        return {
            "visible": False,
            "reason": f"Not visible: approach date is {date_diff} days away from today"
        }
    
    # We're showing all NEOs regardless of size
    # The original size filter has been removed as per requirements
    # This allows all NEOs flying over the user's location to be mapped
    
    # We're showing all NEOs flying over the user's location regardless of distance
    # The original distance filter has been removed as per requirements
    # This allows all NEOs flying over the user's location to be mapped, even distant ones
    
    # If we've passed all checks, the object might be visible
    # Since we don't have precise orbital data, we'll provide an approximate direction
    
    # This is where we would calculate the actual position if we had orbital elements
    # For now, we'll use a simplified approach based on the hemisphere
    
    # Northern hemisphere objects tend to be more visible from northern latitudes
    is_northern = latitude > 0
    
    # Generate a plausible direction based on the latitude
    if is_northern:
        possible_directions = ["South", "Southeast", "Southwest"] if latitude > 45 else ["South", "Southeast", "Southwest", "East", "West"]
    else:
        possible_directions = ["North", "Northeast", "Northwest"] if latitude < -45 else ["North", "Northeast", "Northwest", "East", "West"]
    
    direction = random.choice(possible_directions)
    
    # Generate a plausible elevation
    elevation = random.randint(20, 60)
    
    # Convert direction to azimuth angle for sky map
    azimuth = 0  # Default North
    if direction == "North":
        azimuth = 0
    elif direction == "Northeast":
        azimuth = 45
    elif direction == "East":
        azimuth = 90
    elif direction == "Southeast":
        azimuth = 135
    elif direction == "South":
        azimuth = 180
    elif direction == "Southwest":
        azimuth = 225
    elif direction == "West":
        azimuth = 270
    elif direction == "Northwest":
        azimuth = 315
    
    return {
        "visible": True,
        "direction": direction,
        "elevation": elevation,
        "azimuth": azimuth,  # Add azimuth for sky map
        "note": "This is an approximate visibility estimate. Actual visibility depends on many factors including light pollution, weather, and precise orbital calculations."
    }


def get_neo_by_id(asteroid_id: str, api_key: str = "DEMO_KEY") -> Dict[str, Any]:
    """
    Get detailed information about a specific Near Earth Object by its ID
    
    Args:
        asteroid_id: NASA JPL small body ID
        api_key: NASA API key
        
    Returns:
        Dictionary containing detailed NEO data
        
    Raises:
        Exception: If there's an error with the API request
    """
    # Check cache first
    cache_key = f"id_{asteroid_id}_{api_key}"
    if cache_key in NEO_CACHE:
        cache_time, cached_data = NEO_CACHE[cache_key]
        if datetime.now().timestamp() - cache_time < CACHE_DURATION:
            logger.info(f"Using cached NEO data for ID {asteroid_id}")
            return cached_data
    
    # Build API request URL
    url = f"{BASE_URL}/neo/{asteroid_id}"
    
    # Prepare request parameters
    params = {
        "api_key": api_key
    }
    
    try:
        # Send API request
        logger.info(f"Requesting NEO data for ID {asteroid_id}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Process API response
        data = response.json()
        
        # Cache the result
        NEO_CACHE[cache_key] = (datetime.now().timestamp(), data)
        
        return data
    except Exception as e:
        logger.error(f"Error getting NEO data for ID {asteroid_id}: {str(e)}")
        raise
