#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Planetary Body API Module

This module provides functionality to calculate planetary body positions using the Skyfield library.
It directly uses Skyfield for astronomical calculations without any additional abstraction layers.

Main features:
    - Retrieve information about all visible planetary bodies
    - Retrieve information about specific planetary bodies
    - Support for position calculation based on observer location (latitude, longitude, elevation)
    - Support for specifying observation time
    - Support for retrieving right ascension and declination coordinates
    - Support for filtering to show only planets above the horizon
    - Calculations performed locally using Skyfield library, no internet connection required

Usage example:
    >>> from planets_api import get_visible_planets
    >>> planets = get_visible_planets(latitude=32, longitude=-98)
    >>> for planet in planets:
    ...     print(f"{planet['name']}: Altitude {planet['altitude']}°, Azimuth {planet['azimuth']}°")
"""

import logging
import json
import os
import hashlib
import math
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from datetime import datetime, timedelta
import time

# Skyfield imports
from skyfield.api import load, wgs84, utc
from skyfield import almanac
from skyfield.magnitudelib import planetary_magnitude
from astropy.coordinates import get_constellation
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache settings
CACHE_ENABLED = True
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
CACHE_DURATION = 300  # Cache validity period (seconds)

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

# API基本URL
BASE_URL = "https://api.visibleplanets.dev/v3"

# Load the planetary ephemeris and timescale
try:
    logger.info("Loading planetary ephemeris...")
    ephemeris = load('de421.bsp')  # This file will be downloaded if not present
    ts = load.timescale()
    logger.info("Planetary ephemeris loaded successfully")
    
    # Define planet objects
    SUN = ephemeris['sun']
    MERCURY = ephemeris['mercury barycenter']
    VENUS = ephemeris['venus barycenter']
    EARTH = ephemeris['earth barycenter']
    MARS = ephemeris['mars barycenter']
    JUPITER = ephemeris['jupiter barycenter']
    SATURN = ephemeris['saturn barycenter']
    URANUS = ephemeris['uranus barycenter']
    NEPTUNE = ephemeris['neptune barycenter']
    MOON = ephemeris['moon']
    
    # Add Pluto (dwarf planet)
    try:
        PLUTO = ephemeris['pluto barycenter']
    except KeyError:
        logger.warning("Pluto data not available in ephemeris")
        PLUTO = None
    
    # Add Jupiter's Galilean moons
    try:
        IO = ephemeris['jupiter barycenter'] + ephemeris['io']
        EUROPA = ephemeris['jupiter barycenter'] + ephemeris['europa']
        GANYMEDE = ephemeris['jupiter barycenter'] + ephemeris['ganymede']
        CALLISTO = ephemeris['jupiter barycenter'] + ephemeris['callisto']
    except KeyError:
        logger.warning("Jupiter's moons data not available in ephemeris")
        IO = EUROPA = GANYMEDE = CALLISTO = None
    
    # Add Saturn's major moons
    try:
        TITAN = ephemeris['saturn barycenter'] + ephemeris['titan']
        ENCELADUS = ephemeris['saturn barycenter'] + ephemeris['enceladus']
        MIMAS = ephemeris['saturn barycenter'] + ephemeris['mimas']
        DIONE = ephemeris['saturn barycenter'] + ephemeris['dione']
        RHEA = ephemeris['saturn barycenter'] + ephemeris['rhea']
        IAPETUS = ephemeris['saturn barycenter'] + ephemeris['iapetus']
    except KeyError:
        logger.warning("Saturn's moons data not available in ephemeris")
        TITAN = ENCELADUS = MIMAS = DIONE = RHEA = IAPETUS = None
    
    # Add Uranus's major moons
    try:
        MIRANDA = ephemeris['uranus barycenter'] + ephemeris['miranda']
        ARIEL = ephemeris['uranus barycenter'] + ephemeris['ariel']
        UMBRIEL = ephemeris['uranus barycenter'] + ephemeris['umbriel']
        TITANIA = ephemeris['uranus barycenter'] + ephemeris['titania']
        OBERON = ephemeris['uranus barycenter'] + ephemeris['oberon']
    except KeyError:
        logger.warning("Uranus's moons data not available in ephemeris")
        MIRANDA = ARIEL = UMBRIEL = TITANIA = OBERON = None
    
    # Add Neptune's major moons
    try:
        TRITON = ephemeris['neptune barycenter'] + ephemeris['triton']
        NEREID = ephemeris['neptune barycenter'] + ephemeris['nereid']
    except KeyError:
        logger.warning("Neptune's moons data not available in ephemeris")
        TRITON = NEREID = None
    
    # Dictionary mapping planet names to their Skyfield objects
    PLANETS = {
        'Sun': SUN,
        'Mercury': MERCURY,
        'Venus': VENUS,
        'Mars': MARS,
        'Jupiter': JUPITER,
        'Saturn': SATURN,
        'Uranus': URANUS,
        'Neptune': NEPTUNE,
        'Moon': MOON
    }
    
    # Add additional bodies if available
    if PLUTO is not None:
        PLANETS['Pluto'] = PLUTO
    
    # Add Jupiter's moons if available
    if IO is not None:
        PLANETS['Io'] = IO
    if EUROPA is not None:
        PLANETS['Europa'] = EUROPA
    if GANYMEDE is not None:
        PLANETS['Ganymede'] = GANYMEDE
    if CALLISTO is not None:
        PLANETS['Callisto'] = CALLISTO
    
    # Add Saturn's moons if available
    if TITAN is not None:
        PLANETS['Titan'] = TITAN
    if ENCELADUS is not None:
        PLANETS['Enceladus'] = ENCELADUS
    if MIMAS is not None:
        PLANETS['Mimas'] = MIMAS
    if DIONE is not None:
        PLANETS['Dione'] = DIONE
    if RHEA is not None:
        PLANETS['Rhea'] = RHEA
    if IAPETUS is not None:
        PLANETS['Iapetus'] = IAPETUS
    
    # Add Uranus's moons if available
    if MIRANDA is not None:
        PLANETS['Miranda'] = MIRANDA
    if ARIEL is not None:
        PLANETS['Ariel'] = ARIEL
    if UMBRIEL is not None:
        PLANETS['Umbriel'] = UMBRIEL
    if TITANIA is not None:
        PLANETS['Titania'] = TITANIA
    if OBERON is not None:
        PLANETS['Oberon'] = OBERON
    
    # Add Neptune's moons if available
    if TRITON is not None:
        PLANETS['Triton'] = TRITON
    if NEREID is not None:
        PLANETS['Nereid'] = NEREID
except Exception as e:
    logger.error(f"Error loading planetary ephemeris: {str(e)}")
    raise


class PlanetsAPIError(Exception):
    """Base exception class for Planetary API call errors"""
    pass


class APIDataError(PlanetsAPIError):
    """API data processing error"""
    pass


def cache_result(func: Callable) -> Callable:
    """
    Cache decorator for caching calculation results
    
    Args:
        func: Function whose results to cache
        
    Returns:
        Wrapped function with caching capability
    """
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


def _format_ra_dec(ra_hours: float, dec_degrees: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Format right ascension and declination values into the API format
    
    Args:
        ra_hours: Right ascension in hours
        dec_degrees: Declination in degrees
        
    Returns:
        Tuple of (right ascension dict, declination dict)
    """
    # Process right ascension
    ra_negative = ra_hours < 0
    ra_hours = abs(ra_hours)
    ra_hour_part = int(ra_hours)
    ra_minute_part = int((ra_hours - ra_hour_part) * 60)
    ra_second_part = ((ra_hours - ra_hour_part) * 60 - ra_minute_part) * 60
    
    # Process declination
    dec_negative = dec_degrees < 0
    dec_degrees_abs = abs(dec_degrees)
    dec_degree_part = int(dec_degrees_abs)
    dec_arcminute_part = int((dec_degrees_abs - dec_degree_part) * 60)
    dec_arcsecond_part = ((dec_degrees_abs - dec_degree_part) * 60 - dec_arcminute_part) * 60
    
    # Format right ascension
    ra_formatted = {
        "hours": ra_hour_part,
        "minutes": ra_minute_part,
        "seconds": round(ra_second_part, 2),
        "negative": ra_negative
    }
    
    # Format declination
    dec_formatted = {
        "degrees": dec_degree_part,
        "arcminutes": dec_arcminute_part,
        "arcseconds": round(dec_arcsecond_part, 2),
        "negative": dec_negative
    }
    
    return ra_formatted, dec_formatted


@cache_result
def get_visible_planets(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    elevation: Optional[float] = None,
    time: Optional[Union[str, datetime]] = None,
    show_coords: bool = False,
    above_horizon: bool = True,
    use_offline_mode: bool = False  # Kept for compatibility, not used
) -> List[Dict[str, Any]]:
    """
    Get planetary body data using Skyfield calculations
    
    Args:
        latitude: Observer's latitude (degrees)
        longitude: Observer's longitude (degrees)
        elevation: Observer's elevation (meters)
        time: Observation time, can be ISO 8601 format string or datetime object, defaults to current time
        show_coords: Whether to show planet's right ascension and declination coordinates, defaults to False
        above_horizon: Whether to show only planets above the horizon, defaults to True
        use_offline_mode: Kept for compatibility, not used (all calculations are local)
        
    Returns:
        List containing planetary data, each planet is a dictionary
        
    Raises:
        PlanetsAPIError: Error during calculations or data processing
    """
    try:
        # Set default location if not provided (New York)
        latitude = 40.7128 if latitude is None else latitude
        longitude = -74.0060 if longitude is None else longitude
        elevation = 0 if elevation is None else elevation
        
        # Convert time to datetime object with timezone if it's a string
        time_obj = None
        if time is not None:
            if isinstance(time, str):
                try:
                    # Parse ISO format with timezone if provided
                    time_obj = datetime.fromisoformat(time.replace('Z', '+00:00'))
                    # Ensure timezone info is present
                    if time_obj.tzinfo is None:
                        time_obj = time_obj.replace(tzinfo=utc)
                except ValueError:
                    logger.warning(f"Invalid time format: {time}, using current time")
                    time_obj = datetime.now(tz=utc)
            else:
                # If time is already a datetime object, ensure it has timezone
                time_obj = time if time.tzinfo is not None else time.replace(tzinfo=utc)
        else:
            # Use current time with UTC timezone
            time_obj = datetime.now(tz=utc)
        
        # Create observer location
        observer = wgs84.latlon(latitude, longitude, elevation_m=elevation)
        
        # Convert datetime to Skyfield time
        t = ts.from_datetime(time_obj)
        
        # Calculate positions for all planets
        planets_data = []
        
        # Get Earth position for topocentric calculations
        earth = ephemeris['earth']
        
        for name, planet in PLANETS.items():
            try:
                # Calculate planet position from observer's location
                apparent_position = (earth + observer).at(t).observe(planet).apparent()
                
                # Get altitude and azimuth
                alt, az, distance = apparent_position.altaz()
                altitude = alt.degrees
                azimuth = az.degrees
                
                # Calculate magnitude
                if name == 'Moon':
                    # Moon magnitude calculation is special
                    magnitude = -12.5  # Approximate average magnitude
                elif name == 'Sun':
                    magnitude = -26.7  # Approximate solar magnitude
                else:
                    try:
                        # Try to calculate magnitude using Skyfield
                        sun_position = (earth + observer).at(t).observe(SUN).apparent()
                        magnitude = planetary_magnitude(planet, earth, sun_position, t)
                    except Exception:
                        # Fallback to approximate magnitudes
                        magnitudes = {
                            'Mercury': -0.5, 'Venus': -4.2, 'Mars': 1.2, 
                            'Jupiter': -2.3, 'Saturn': 0.8, 'Uranus': 5.7, 
                            'Neptune': 7.9
                        }
                        magnitude = magnitudes.get(name, 0)
                
                # Get equatorial coordinates (RA and Dec)
                ra, dec, _ = apparent_position.radec()
                ra_hours = ra.hours
                dec_degrees = dec.degrees
                
                # Get constellation
                try:
                    # Convert RA from hours to degrees
                    ra_degrees = ra_hours * 15
                    constellation = get_constellation(ra_degrees * math.pi / 180, dec_degrees * math.pi / 180)
                except Exception:
                    constellation = "Unknown"
                
                # Create planet data dictionary
                planet_data = {
                    "name": name,
                    "altitude": round(altitude, 2),
                    "azimuth": round(azimuth, 2),
                    "magnitude": round(magnitude, 2),
                    "constellation": constellation
                }
                
                # Add celestial coordinates if requested
                if show_coords:
                    ra_formatted, dec_formatted = _format_ra_dec(ra_hours, dec_degrees)
                    planet_data["rightAscension"] = ra_formatted
                    planet_data["declination"] = dec_formatted
                
                planets_data.append(planet_data)
                
            except Exception as e:
                logger.warning(f"Error calculating position for {name}: {str(e)}")
        
        # Filter planets below horizon if requested
        if above_horizon:
            planets_data = [p for p in planets_data if p.get('altitude', -90) > 0]
        
        return planets_data
        
    except Exception as e:
        logger.error(f"Error getting planet data: {str(e)}")
        raise APIDataError(f"Error getting planet data: {str(e)}") from e


def get_planet_by_name(
    planet_name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    elevation: Optional[float] = None,
    time: Optional[Union[str, datetime]] = None,
    show_coords: bool = True,
    use_offline_mode: bool = False  # Kept for compatibility, not used
) -> Optional[Dict[str, Any]]:
    """
    Get data for a specific planet by name
    
    Args:
        planet_name: Name of the planet to get data for
        latitude: Observer's latitude
        longitude: Observer's longitude
        elevation: Observer's elevation (meters)
        time: Observation time
        show_coords: Whether to show planet's right ascension and declination coordinates, defaults to True
        use_offline_mode: Kept for compatibility, not used (all calculations are local)
        
    Returns:
        Dictionary containing planet data or None if planet not found
        
    Raises:
        PlanetsAPIError: Error during calculations or data processing
    """
    # Get data for all planets
    planets_data = get_visible_planets(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        time=time,
        show_coords=show_coords,
        above_horizon=False  # Get all planets, not just those above horizon
    )
    
    # Find the specified planet
    for planet in planets_data:
        if planet['name'].lower() == planet_name.lower():
            return planet
            
    # Planet not found
    return None


def get_moon_phase(time_obj: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate the current moon phase
    
    Args:
        time_obj: Observation time, defaults to current time
        
    Returns:
        Dictionary containing moon phase information
    """
    # Use current time if not provided
    if time_obj is None:
        time_obj = datetime.now(tz=utc)
    elif time_obj.tzinfo is None:
        # Ensure timezone info is present
        time_obj = time_obj.replace(tzinfo=utc)
    
    # Convert to Skyfield time
    t = ts.from_datetime(time_obj)
    
    # Calculate moon phase
    earth = ephemeris['earth']
    sun = ephemeris['sun']
    moon = ephemeris['moon']
    
    e = earth.at(t)
    s = e.observe(sun).apparent()
    m = e.observe(moon).apparent()
    
    # Calculate elongation and phase angle
    _, slon, _ = s.ecliptic_latlon()
    _, mlon, _ = m.ecliptic_latlon()
    
    # Calculate phase as a percentage (0 = new, 50 = quarter, 100 = full)
    phase_angle = (mlon.degrees - slon.degrees) % 360
    if phase_angle > 180:
        phase_angle = 360 - phase_angle
    
    # Convert to percentage
    phase_percent = phase_angle / 180 * 100
    
    # Determine phase name
    if phase_percent < 1:
        phase_name = "New Moon"
    elif phase_percent < 25:
        phase_name = "Waxing Crescent"
    elif phase_percent < 49:
        phase_name = "First Quarter"
    elif phase_percent < 51:
        phase_name = "First Quarter"
    elif phase_percent < 75:
        phase_name = "Waxing Gibbous"
    elif phase_percent < 99:
        phase_name = "Full Moon"
    elif phase_percent < 100:
        phase_name = "Waning Gibbous"
    else:
        phase_name = "Last Quarter"
    
    # Calculate distance
    distance = m.distance().km
    
    # Calculate angular diameter
    angular_diameter_degrees = 2 * math.atan(1737.4 / distance) * 180 / math.pi
    
    return {
        "date": time_obj.strftime("%Y-%m-%d"),
        "phase_percent": round(phase_percent, 1),
        "phase_name": phase_name,
        "distance_km": round(distance),
        "angular_diameter_degrees": round(angular_diameter_degrees, 4)
    }


def get_twilight_times(
    latitude: float,
    longitude: float,
    date_obj: Optional[datetime] = None,
    twilight_type: str = 'civil'
) -> Dict[str, Any]:
    """
    Calculate twilight times for a specific location and date
    
    Args:
        latitude: Observer's latitude in degrees
        longitude: Observer's longitude in degrees
        date_obj: Date, defaults to current date
        twilight_type: Type of twilight ('civil', 'nautical', or 'astronomical')
        
    Returns:
        Dictionary containing twilight times
    """
    # Use current date if not provided
    if date_obj is None:
        date_obj = datetime.now(tz=utc)
    elif date_obj.tzinfo is None:
        # Ensure timezone info is present
        date_obj = date_obj.replace(tzinfo=utc)
    
    # Create observer location
    observer = wgs84.latlon(latitude, longitude)
    
    # Set twilight depression angle
    if twilight_type == 'civil':
        depression_angle = 6.0
    elif twilight_type == 'nautical':
        depression_angle = 12.0
    elif twilight_type == 'astronomical':
        depression_angle = 18.0
    else:
        logger.warning(f"Invalid twilight type: {twilight_type}, using civil twilight")
        depression_angle = 6.0
    
    # Calculate times
    try:
        t0 = ts.from_datetime(datetime(date_obj.year, date_obj.month, date_obj.day, tzinfo=utc))
        t1 = ts.from_datetime(datetime(date_obj.year, date_obj.month, date_obj.day + 1, tzinfo=utc))
        
        f = almanac.dark_twilight_day(ephemeris, observer)
        times, events = almanac.find_discrete(t0, t1, f)
        
        # Process results
        result = {"type": twilight_type}
        
        for time, event in zip(times, events):
            if event == (1 - depression_angle / 90.0):  # Dawn
                result["dawn"] = time.utc_datetime().strftime("%H:%M:%S")
            elif event == (1 + depression_angle / 90.0):  # Dusk
                result["dusk"] = time.utc_datetime().strftime("%H:%M:%S")
        
        return result
    except Exception as e:
        logger.warning(f"Error calculating twilight times: {str(e)}")
        return {"type": twilight_type, "error": str(e)}


def get_api_meta_info(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    use_offline_mode: bool = False  # Kept for compatibility, not used
) -> Dict[str, Any]:
    """
    Get API metadata information
    
    Args:
        latitude: Observer's latitude
        longitude: Observer's longitude
        use_offline_mode: Kept for compatibility, not used (all calculations are local)
        
    Returns:
        Dictionary containing API metadata
    """
    # Set default location if not provided
    latitude = 40.7128 if latitude is None else latitude
    longitude = -74.0060 if longitude is None else longitude
    
    # Return metadata
    return {
        "engineVersion": f"Skyfield {load.__version__}",
        "timestamp": datetime.now().isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "elevation": 0,
        "calculationType": "skyfield"
    }


def format_planet_info(planet_data: Dict[str, Any], detailed: bool = False) -> str:
    """
    Format planet information as a readable string
    
    Args:
        planet_data: Planet data dictionary
        detailed: Whether to include detailed information
        
    Returns:
        Formatted planet information string
    """
    name = planet_data.get('name', 'Unknown')
    altitude = planet_data.get('altitude')
    azimuth = planet_data.get('azimuth')
    magnitude = planet_data.get('magnitude')
    constellation = planet_data.get('constellation', '')
    
    # Basic information
    info = f"{name}"
    
    if altitude is not None and azimuth is not None:
        info += f": Altitude {altitude:.1f}°, Azimuth {azimuth:.1f}°"
        
    if magnitude is not None:
        info += f", Magnitude {magnitude:.1f}"
        
    if constellation:
        info += f", in {constellation}"
    
    # Add detailed information if requested
    if detailed and 'rightAscension' in planet_data and 'declination' in planet_data:
        ra = planet_data['rightAscension']
        dec = planet_data['declination']
        
        ra_str = f"{ra['hours']}h {ra['minutes']}m {ra['seconds']:.2f}s"
        if ra.get('negative', False):
            ra_str = f"-{ra_str}"
            
        dec_str = f"{dec['degrees']}° {dec['arcminutes']}' {dec['arcseconds']:.2f}\""
        if dec.get('negative', False):
            dec_str = f"-{dec_str}"
            
        info += f"\nRight Ascension: {ra_str}"
        info += f"\nDeclination: {dec_str}"
    
    return info


# For compatibility with the original module
def set_offline_mode(enabled: bool = True) -> None:
    """
    Enable or disable offline mode (kept for compatibility, does nothing)
    
    Args:
        enabled: Whether to enable offline mode
    """
    logger.info(f"Offline mode setting ignored, using Skyfield calculations")


def is_offline_mode() -> bool:
    """
    Check if currently in offline mode (kept for compatibility, always returns False)
    
    Returns:
        False (all calculations are done locally with Skyfield)
    """
    return False


def clear_cache() -> None:
    """
    Clear all cached data
    """
    try:
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR, exist_ok=True)
            logger.info("Cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise
