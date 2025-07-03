#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Astronomical Calculation Utilities Module

This module provides utility functions related to astronomical calculations, particularly those related to
planet positions and visibility. Main features include determining planet visibility, converting astronomical
coordinates to user-friendly descriptions, calculating optimal observation times, and identifying the constellation
that a planet is in.

Main features:
    - Determining if a planet is visible (based on altitude, azimuth, etc.)
    - Converting astronomical coordinates (right ascension, declination) to user-friendly descriptions
    - Calculating optimal observation times for planets
    - Determining which constellation a planet is in
    - Other astronomical calculation helper functions

Usage examples:
    >>> from astronomy_utils import is_planet_visible, get_sky_position_description
    >>> visible = is_planet_visible(altitude=30, magnitude=0)
    >>> print(visible)  # True
    >>> description = get_sky_position_description(altitude=30, azimuth=135)
    >>> print(description)  # "Look Southeast, at an altitude of about 30 degrees"
"""

import math
import logging
import os
import json
import functools
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from datetime import datetime, timedelta

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, get_constellation
from astropy.time import Time
from astropy.coordinates import solar_system_ephemeris, get_body
from skyfield.api import load, wgs84
from skyfield.magnitudelib import planetary_magnitude

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
# Azimuth to direction name mapping
AZIMUTH_DIRECTIONS = {
    0: "North",
    45: "Northeast",
    90: "East",
    135: "Southeast",
    180: "South",
    225: "Southwest",
    270: "West",
    315: "Northwest",
    360: "North"
}

# Planet name mapping (English to English - kept for compatibility)
PLANET_NAMES = {
    "mercury": "Mercury",
    "venus": "Venus",
    "earth": "Earth",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",  # Not a planet anymore, but still a common celestial body
    "moon": "Moon",
    "sun": "Sun"
}

# Magnitude threshold definitions
NAKED_EYE_MAGNITUDE = 6.0  # Dimmest magnitude visible to the naked eye
URBAN_MAGNITUDE = 3.0      # Dimmest magnitude visible to the naked eye in urban areas
BRIGHT_MAGNITUDE = 0.0     # Threshold for bright celestial bodies

# Altitude threshold definitions
HORIZON_ALTITUDE = 0.0     # Horizon altitude
GOOD_VISIBILITY_ALTITUDE = 15.0  # Minimum altitude for good visibility
OPTIMAL_VISIBILITY_ALTITUDE = 30.0  # Minimum altitude for optimal visibility

# Astronomical twilight definitions
CIVIL_TWILIGHT = -6.0      # Civil twilight (sun center is 6 degrees below the horizon)
NAUTICAL_TWILIGHT = -12.0  # Nautical twilight (sun center is 12 degrees below the horizon)
ASTRONOMICAL_TWILIGHT = -18.0  # Astronomical twilight (sun center is 18 degrees below the horizon)

# Cache settings
CACHE_ENABLED = True
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "astronomy")
CACHE_DURATION = 3600  # Cache validity period (seconds)

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)


def is_planet_visible(altitude: float, magnitude: Optional[float] = None, 
                      min_altitude: float = HORIZON_ALTITUDE, 
                      max_magnitude: Optional[float] = None) -> bool:
    """
    Determine if a planet is visible
    
    Based on the planet's altitude and brightness (magnitude), determines if it is visible.
    Takes into account atmospheric extinction and horizon obstruction.
    
    Args:
        altitude: Planet altitude angle (degrees)
        magnitude: Planet visual magnitude, lower values indicate brighter objects
        min_altitude: Minimum visible altitude (degrees), defaults to the horizon (0 degrees)
        max_magnitude: Maximum visible magnitude, defaults to None (no magnitude restriction)
        
    Returns:
        Boolean indicating whether the planet is visible
        
    Notes:
        - Celestial bodies with altitude below the horizon (0 degrees) are typically not visible
        - Celestial bodies with magnitude greater than 6.0 are typically not visible to the naked eye
        - In urban light pollution conditions, celestial bodies with magnitude greater than 3.0 are typically not visible to the naked eye
    """
    # Check if altitude meets visibility condition
    if altitude < min_altitude:
        logger.debug(f"Planet altitude {altitude:.2f}° is below minimum visible altitude {min_altitude:.2f}°")
        return False
        
    # If magnitude and maximum visible magnitude threshold are provided, check if magnitude meets visibility condition
    if magnitude is not None and max_magnitude is not None:
        if magnitude > max_magnitude:
            logger.debug(f"Planet magnitude {magnitude:.2f} is above maximum visible magnitude {max_magnitude:.2f}")
            return False
            
    # Consider atmospheric extinction effect
    # At low altitudes, atmospheric extinction is more severe
    if altitude < 10.0 and magnitude is not None:
        # Simplified model: increase effective magnitude at low altitudes (making the body appear dimmer)
        effective_magnitude = magnitude + (10.0 - altitude) * 0.2
        if max_magnitude is not None and effective_magnitude > max_magnitude:
            logger.debug(f"Considering atmospheric extinction, planet effective magnitude {effective_magnitude:.2f} is above maximum visible magnitude {max_magnitude:.2f}")
            return False
    
    # Passed all checks, consider the planet visible
    return True


def get_azimuth_direction(azimuth: float) -> str:
    """
    Convert azimuth angle to direction description
    
    Args:
        azimuth: Azimuth angle (degrees), range 0-360, 0 is North, 90 is East, etc.
        
    Returns:
        Direction description string, such as "Southeast"
    """
    # Ensure azimuth is in the 0-360 range
    azimuth = azimuth % 360
    
    # Find the closest direction
    closest_direction = min(AZIMUTH_DIRECTIONS.keys(), key=lambda x: abs(x - azimuth))
    
    # If azimuth is between two cardinal directions, return a combined direction
    if abs(azimuth - closest_direction) > 22.5:
        # Find the two closest cardinal directions
        directions = sorted(AZIMUTH_DIRECTIONS.keys(), key=lambda x: abs(x - azimuth))
        dir1, dir2 = directions[0], directions[1]
        
        # Ensure direction order is correct (clockwise)
        if (dir1 > dir2 and not (dir1 > 270 and dir2 < 90)) or (dir1 < 90 and dir2 > 270):
            dir1, dir2 = dir2, dir1
            
        # Return combined direction
        return f"{AZIMUTH_DIRECTIONS[dir1]}-{AZIMUTH_DIRECTIONS[dir2]}"
    else:
        return AZIMUTH_DIRECTIONS[closest_direction]


def get_altitude_description(altitude: float) -> str:
    """
    Convert altitude angle to descriptive text
    
    Args:
        altitude: Altitude angle (degrees)
        
    Returns:
        Altitude description string, such as "low", "medium height", "high"
    """
    if altitude < 0:
        return "below the horizon"
    elif altitude < 15:
        return "low"
    elif altitude < 45:
        return "at medium height"
    elif altitude < 75:
        return "high"
    else:
        return "almost directly overhead"


def get_sky_position_description(altitude: float, azimuth: float, 
                                language: str = 'en') -> str:
    """
    Convert astronomical coordinates (altitude, azimuth) to a user-friendly description
    
    Args:
        altitude: Altitude angle (degrees)
        azimuth: Azimuth angle (degrees)
        language: Language code, default is 'en' (English)

    Returns:
        User-friendly description of the position in the sky
    """
    # Get direction based on azimuth
    direction = get_azimuth_direction(azimuth)
    
    # Get altitude description
    altitude_desc = get_altitude_description(altitude)
    
    # Format description based on language
    if language == 'en':
        return f"looking {direction}, {altitude_desc} ({altitude:.1f}°)"
    else:
        # Default to English if language not supported
        return f"looking {direction}, {altitude_desc} ({altitude:.1f}°)"


def calculate_best_observation_time(planet_name: str, latitude: float, longitude: float,
                                   start_time: Optional[datetime] = None,
                                   days_ahead: int = 7) -> Dict[str, Any]:
    """
    Calculate the best time to observe a planet in the coming days
    
    Args:
        planet_name: Name of the planet
        latitude: Observer's latitude
        longitude: Observer's longitude
        start_time: Start time for calculation, defaults to current time
        days_ahead: Number of days to look ahead, defaults to 7
        
    Returns:
        Dictionary with best observation time and related information
    """
    # This is a placeholder function
    # In a real implementation, this would calculate the best observation time
    # based on when the planet is highest in the sky, during night time, etc.
    
    # For now, just return a dummy result
    if start_time is None:
        start_time = datetime.now()
        
    best_time = start_time + timedelta(days=1)
    
    return {
        "planet": planet_name,
        "best_time": best_time,
        "altitude": 45.0,  # Dummy value
        "azimuth": 180.0,  # Dummy value
        "reason": "This is a placeholder. In a real implementation, this would be calculated based on when the planet is highest in the sky during night time."
    }


def get_moon_phase(time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate the moon phase for a given time
    
    Args:
        time: Time for which to calculate the moon phase, defaults to current time
        
    Returns:
        Dictionary with moon phase information
    """
    # This is a placeholder function
    # In a real implementation, this would calculate the moon phase
    
    # For now, just return a dummy result
    if time is None:
        time = datetime.now()
        
    return {
        "time": time,
        "phase_name": "First Quarter",  # Dummy value
        "phase_angle": 90.0,  # Dummy value
        "illumination": 0.5,  # Dummy value
        "description": "This is a placeholder. In a real implementation, this would provide the actual moon phase."
    }


def calculate_twilight_times(latitude: float, longitude: float, 
                            date: Optional[datetime] = None) -> Dict[str, datetime]:
    """
    Calculate civil, nautical, and astronomical twilight times
    
    Args:
        latitude: Observer's latitude
        longitude: Observer's longitude
        date: Date for which to calculate twilight times, defaults to current date
        
    Returns:
        Dictionary with twilight times
    """
    # This is a placeholder function
    # In a real implementation, this would calculate the twilight times
    
    # For now, just return dummy results
    if date is None:
        date = datetime.now()
        
    # Create dummy times
    base_time = datetime.combine(date.date(), datetime.min.time())
    
    return {
        "civil_dawn": base_time + timedelta(hours=5, minutes=30),
        "sunrise": base_time + timedelta(hours=6),
        "sunset": base_time + timedelta(hours=18),
        "civil_dusk": base_time + timedelta(hours=18, minutes=30),
        "nautical_dusk": base_time + timedelta(hours=19),
        "astronomical_dusk": base_time + timedelta(hours=19, minutes=30),
        "astronomical_dawn": base_time + timedelta(hours=4, minutes=30),
        "nautical_dawn": base_time + timedelta(hours=5),
    }


def cache_result(func: Callable) -> Callable:
    """
    Cache decorator for caching function results
    
    Args:
        func: Function whose results to cache
        
    Returns:
        Wrapped function with caching capability
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not CACHE_ENABLED:
            return func(*args, **kwargs)
            
        # Generate cache key
        cache_key = _generate_cache_key(func.__name__, args, kwargs)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        # Check if cache exists and is still valid
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                cache_time = cached_data.get('_cache_time', 0)
                current_time = time.time()
                
                if current_time - cache_time <= CACHE_DURATION:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data.get('result')
                    
                logger.debug(f"Cache expired for {func.__name__}")
            except Exception as e:
                logger.warning(f"Error reading cache: {str(e)}")
        
        # Cache miss or expired, call the function
        result = func(*args, **kwargs)
        
        # Save to cache
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'result': result,
                    '_cache_time': time.time()
                }, f)
            logger.debug(f"Cached result for {func.__name__}")
        except Exception as e:
            logger.warning(f"Error writing cache: {str(e)}")
            
        return result
        
    return wrapper


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a cache key for a function call
    
    Args:
        func_name: Function name
        args: Function positional arguments
        kwargs: Function keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a string representation of the arguments
    args_str = str(args) + str(sorted(kwargs.items()))
    
    # Create a hash of the arguments
    args_hash = hashlib.md5(args_str.encode()).hexdigest()
    
    # Combine function name and arguments hash
    return f"{func_name}_{args_hash}"
