#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Planetary Body Tracker

This application uses Streamlit to create a user-friendly interface that allows users to view and track planetary bodies in the sky.
It integrates the planets_api.py and astronomy_utils.py modules to implement planet data retrieval and astronomical calculations.

Main features:
    - Users can input location (longitude, latitude, elevation) and time
    - Visual display of planets in the sky
    - Detailed information queries for specific planets
    - Planet visibility calculation based on user location
    - User-friendly descriptions of planet positions in the sky
    - Display of moon phases and other astronomical information
    - Offline mode with simulated data when API is unavailable

Usage:
    Run command: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import os
import sys
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
import time

# Set matplotlib backend to Agg to avoid GUI thread issues
import matplotlib
os.environ["MPLBACKEND"] = "Agg"
matplotlib.use('Agg', force=True)
plt.rcParams['axes.unicode_minus'] = False  # Properly display minus signs

# Import custom modules
import planets_api
import astronomy_utils
import solar_system_3d  # Import 3D solar system visualization module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_LATITUDE = 40.7128  # New York latitude
DEFAULT_LONGITUDE = -74.0060  # New York longitude
DEFAULT_ELEVATION = 10  # Default elevation (meters)

# Preset locations (North American cities)
PRESET_LOCATIONS = {
    "New York": (40.7128, -74.0060, 10),
    "Los Angeles": (34.0522, -118.2437, 93),
    "Chicago": (41.8781, -87.6298, 182),
    "Toronto": (43.6532, -79.3832, 76),
    "Vancouver": (49.2827, -123.1207, 0),
    "Mexico City": (19.4326, -99.1332, 2250),
    "San Francisco": (37.7749, -122.4194, 16),
    "Seattle": (47.6062, -122.3321, 53),
    "Miami": (25.7617, -80.1918, 2),
    "Denver": (39.7392, -104.9903, 1609)
}

# Planet color mapping
PLANET_COLORS = {
    # Planets
    "Mercury": "#c0c0c0",  # Mercury - silver
    "Venus": "#f9d71c",    # Venus - yellow
    "Earth": "#1e90ff",    # Earth - blue
    "Mars": "#ff4500",     # Mars - red
    "Jupiter": "#ffa500",  # Jupiter - orange
    "Saturn": "#f0e68c",   # Saturn - light yellow
    "Uranus": "#40e0d0",   # Uranus - turquoise
    "Neptune": "#0000cd",  # Neptune - deep blue
    "Moon": "#f8f8ff",     # Moon - white
    "Sun": "#ffff00",      # Sun - yellow
    
    # Dwarf planets
    "Pluto": "#a0522d",    # Pluto - brown
    
    # Jupiter's moons (Galilean satellites)
    "Io": "#ffcc00",       # Io - yellow-orange (volcanic)
    "Europa": "#ffffff",   # Europa - white (icy)
    "Ganymede": "#c0c0c0", # Ganymede - silver-gray
    "Callisto": "#8b4513", # Callisto - brown (cratered)
    
    # Saturn's moons
    "Titan": "#ffd700",      # Titan - golden (thick atmosphere)
    "Enceladus": "#e0ffff",  # Enceladus - light cyan (icy geysers)
    "Mimas": "#f5f5f5",      # Mimas - white/light gray (heavily cratered)
    "Dione": "#d3d3d3",      # Dione - light gray
    "Rhea": "#c0c0c0",       # Rhea - silver/gray
    "Iapetus": "#f5deb3",    # Iapetus - wheat (two-toned)
    
    # Uranus's moons
    "Miranda": "#b0e0e6",    # Miranda - powder blue
    "Ariel": "#add8e6",      # Ariel - light blue
    "Umbriel": "#778899",    # Umbriel - light slate gray (dark)
    "Titania": "#b0c4de",    # Titania - light steel blue
    "Oberon": "#a9a9a9",     # Oberon - dark gray
    
    # Neptune's moons
    "Triton": "#afeeee",     # Triton - pale turquoise
    "Nereid": "#87ceeb"      # Nereid - sky blue
}


# Use Streamlit's caching mechanism to optimize chart creation
@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_sky_map(planets_data: List[Dict[str, Any]], title: str = "Planetary Bodies in the Sky") -> go.Figure:
    """
    Create a sky map showing the positions of planets in the sky
    
    Args:
        planets_data: List of planetary data
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    # Create polar chart
    fig = go.Figure()
    
    # Add horizon circle (altitude = 0 degrees)
    theta = np.linspace(0, 2*np.pi, 100)
    r = np.ones(100) * 90  # Horizon corresponds to zenith distance of 90 degrees
    fig.add_trace(go.Scatterpolar(
        r=r,
        theta=np.degrees(theta),
        mode='lines',
        line=dict(color='gray', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add altitude degree circles (30 and 60 degrees)
    for altitude in [30, 60]:
        r = np.ones(100) * (90 - altitude)
        fig.add_trace(go.Scatterpolar(
            r=r,
            theta=np.degrees(theta),
            mode='lines',
            line=dict(color='lightgray', width=0.5, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add direction markers (N, E, S, W)
    directions = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
    for direction, angle in directions.items():
        fig.add_trace(go.Scatterpolar(
            r=[95],  # Slightly beyond the horizon
            theta=[angle],
            mode='text',
            text=[direction],
            textfont=dict(size=12, color='black'),
            showlegend=False
        ))
    
    # Categorize celestial bodies
    planets = []
    moons = []
    dwarf_planets = []
    other_bodies = []
    
    for body in planets_data:
        name = body.get('name', 'Unknown')
        
        if name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
            planets.append(body)
        elif name == 'Sun':
            planets.append(body)  # Include Sun with planets for display
        elif name == 'Moon':
            moons.append(body)  # Earth's Moon
        elif name == 'Pluto':
            dwarf_planets.append(body)
        # Jupiter's moons
        elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
            moons.append(body)  # Jupiter's moons
        # Saturn's moons
        elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
            moons.append(body)  # Saturn's moons
        # Uranus's moons
        elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
            moons.append(body)  # Uranus's moons
        # Neptune's moons
        elif name in ['Triton', 'Nereid']:
            moons.append(body)  # Neptune's moons
        else:
            other_bodies.append(body)
    
    # Function to add body to the chart
    def add_body_to_chart(body, symbol=None, text_position="top center"):
        name = body.get('name', 'Unknown')
        altitude = body.get('altitude')
        azimuth = body.get('azimuth')
        magnitude = body.get('magnitude', 0)
        
        # Skip bodies below the horizon
        if altitude is None or altitude < 0:
            return
        
        # Calculate zenith distance (90 degrees - altitude)
        zenith_distance = 90 - altitude
        
        # Determine point size (based on magnitude, smaller magnitude = brighter = larger point)
        size = max(8, 15 - magnitude)  # Minimum point size is 8
        
        # Adjust size for different body types
        if name == 'Sun':
            size = 18  # Sun is largest
        elif name == 'Moon':
            size = 16  # Moon is second largest
        elif name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
            size = max(10, size)  # Ensure planets have good visibility
        elif name == 'Pluto':
            size = max(7, size)  # Dwarf planets slightly smaller
        # Jupiter's moons
        elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
            size = max(6, size)  # Jupiter's moons are medium-sized
        # Saturn's moons
        elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
            size = max(5, size)  # Saturn's moons are smaller
        # Uranus's moons
        elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
            size = max(4, size)  # Uranus's moons are even smaller
        # Neptune's moons
        elif name in ['Triton', 'Nereid']:
            size = max(4, size)  # Neptune's moons are also small
        
        # Determine point color
        color = PLANET_COLORS.get(name, "#808080")  # Default to gray
        
        # Determine marker symbol
        if symbol is None:
            if name == 'Sun':
                symbol = 'circle'
            elif name == 'Moon':
                symbol = 'circle'
            elif name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
                symbol = 'circle'
            elif name == 'Pluto':
                symbol = 'diamond'
            # Jupiter's moons
            elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
                symbol = 'circle-open'
            # Saturn's moons
            elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
                symbol = 'circle-open'
            # Uranus's moons
            elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
                symbol = 'circle-open-dot'
            # Neptune's moons
            elif name in ['Triton', 'Nereid']:
                symbol = 'circle-open-dot'
            else:
                symbol = 'x'
        
        # Add body point
        fig.add_trace(go.Scatterpolar(
            r=[zenith_distance],
            theta=[azimuth],
            mode='markers+text',
            marker=dict(size=size, color=color, symbol=symbol),
            text=[name],
            textposition=text_position,
            name=name,
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Type: {get_body_type(name)}<br>"
                f"Altitude: %{{customdata[0]:.1f}}°<br>"
                f"Azimuth: %{{customdata[1]:.1f}}°<br>"
                f"Magnitude: %{{customdata[2]:.2f}}"
            ),
            customdata=[[altitude, azimuth, magnitude]],
            showlegend=True
        ))
    
    # Helper function to get body type
    def get_body_type(name):
        if name == 'Sun':
            return "Star"
        elif name == 'Moon':
            return "Moon (Earth)"
        elif name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
            return "Planet"
        elif name == 'Pluto':
            return "Dwarf Planet"
        elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
            return f"Moon (Jupiter)"
        elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
            return f"Moon (Saturn)"
        elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
            return f"Moon (Uranus)"
        elif name in ['Triton', 'Nereid']:
            return f"Moon (Neptune)"
        else:
            return "Other"
    
    # Add all bodies to chart
    for body in planets:
        add_body_to_chart(body)
    
    for body in dwarf_planets:
        add_body_to_chart(body)
    
    for body in moons:
        add_body_to_chart(body)
    
    for body in other_bodies:
        add_body_to_chart(body)
    
    # Set chart layout
    fig.update_layout(
        title=dict(text=title, x=0.5),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 90],
                tickmode='array',
                tickvals=[0, 30, 60, 90],
                ticktext=['90°', '60°', '30°', '0°'],
                tickfont=dict(size=10),
                tickangle=0,
            ),
            angularaxis=dict(
                visible=True,
                tickmode='array',
                tickvals=[0, 90, 180, 270],
                ticktext=['N', 'E', 'S', 'W'],
                direction='clockwise',
                rotation=90,
            ),
            bgcolor='aliceblue',
        ),
        showlegend=True,
        legend=dict(
            title="Planets",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


# Helper function to get body type for DataFrame
def get_body_type_for_df(name):
    if name == 'Sun':
        return "Star"
    elif name == 'Moon':
        return "Moon (Earth)"
    elif name in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
        return "Planet"
    elif name == 'Pluto':
        return "Dwarf Planet"
    elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
        return "Moon (Jupiter)"
    elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
        return "Moon (Saturn)"
    elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
        return "Moon (Uranus)"
    elif name in ['Triton', 'Nereid']:
        return "Moon (Neptune)"
    else:
        return "Other"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def format_planet_data_as_df(planets_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Format planetary data as a pandas DataFrame for display
    
    Args:
        planets_data: List of planetary data
        
    Returns:
        Formatted DataFrame
    """
    # Extract relevant data
    formatted_data = []
    for planet in planets_data:
        # Extract basic information
        name = planet.get('name', 'Unknown')
        altitude = planet.get('altitude')
        azimuth = planet.get('azimuth')
        magnitude = planet.get('magnitude')
        constellation = planet.get('constellation', '')
        
        # Determine visibility
        visible = altitude is not None and altitude > 0
        
        # Get user-friendly direction
        direction = astronomy_utils.get_azimuth_direction(azimuth) if azimuth is not None else ""
        
        # Determine body type
        body_type = get_body_type_for_df(name)
        
        # Format data
        data_entry = {
            'Name': name,
            'Type': body_type,
            'Altitude': f"{altitude:.1f}°" if altitude is not None else "N/A",
            'Azimuth': f"{azimuth:.1f}°" if azimuth is not None else "N/A",
            'Direction': direction,
            'Magnitude': f"{magnitude:.2f}" if magnitude is not None else "N/A",
            'Constellation': constellation,
            'Visible': "Yes" if visible else "No"
        }
        
        # Add data source information
        data_entry['Data Source'] = "Skyfield"
        formatted_data.append(data_entry)
    
    # Create DataFrame and sort by visibility and name
    df = pd.DataFrame(formatted_data)
    df = df.sort_values(by=['Visible', 'Name'], ascending=[False, True])
    
    return df


def get_planet_position_info(planet_data: Dict[str, Any], language: str = 'en') -> str:
    """
    Get user-friendly description of planet position
    
    Args:
        planet_data: Planet data dictionary
        language: Language code, default is 'en' (English)
        
    Returns:
        User-friendly position description
    """
    # Extract data
    name = planet_data.get('name', 'Unknown')
    altitude = planet_data.get('altitude')
    azimuth = planet_data.get('azimuth')
    
    # Check if planet is below horizon
    if altitude is None or altitude < 0:
        return f"{name} is currently below the horizon and not visible."
    
    # Get position description
    position_desc = astronomy_utils.get_sky_position_description(altitude, azimuth, language)
    
    # Create description
    description = f"{name} is currently at {position_desc}."
    
    return description


def app_header():
    """Display application header and introduction"""
    st.title("Planetary Body Tracker")
    
    st.markdown("""
    This application allows you to track the positions of planetary bodies in the sky based on your location and time.
    You can see which planets are visible, where to look for them, and get detailed information about each planet.
    """)


def display_calculation_info():
    """Display information about the calculation method"""
    # Function kept for compatibility, but doesn't display anything
    pass


def location_time_sidebar():
    """Create sidebar for location and time inputs"""
    with st.sidebar:
        st.header("Observation Settings")
        
        # Location selection
        st.subheader("Location")
        
        # Option to use preset locations or custom location
        location_option = st.radio(
            "Select location method:",
            ["Preset Cities", "Custom Coordinates"]
        )
        
        if location_option == "Preset Cities":
            # Dropdown for preset cities
            selected_city = st.selectbox(
                "Select a city:",
                list(PRESET_LOCATIONS.keys())
            )
            latitude, longitude, elevation = PRESET_LOCATIONS[selected_city]
            
            # Display the coordinates
            st.info(f"Coordinates: {latitude:.4f}°, {longitude:.4f}°, Elevation: {elevation}m")
            
        else:
            # Custom coordinates input
            col1, col2 = st.columns(2)
            with col1:
                latitude = st.number_input(
                    "Latitude (°):",
                    min_value=-90.0, max_value=90.0, value=DEFAULT_LATITUDE,
                    format="%.4f", step=0.1
                )
            with col2:
                longitude = st.number_input(
                    "Longitude (°):",
                    min_value=-180.0, max_value=180.0, value=DEFAULT_LONGITUDE,
                    format="%.4f", step=0.1
                )
            
            elevation = st.number_input(
                "Elevation (meters):",
                min_value=0, value=DEFAULT_ELEVATION, step=10
            )
        
        # Time selection
        st.subheader("Time")
        
        # Option to use current time or custom time
        time_option = st.radio(
            "Select time:",
            ["Current Time", "Custom Time"]
        )
        
        if time_option == "Current Time":
            observation_time = datetime.now()
            st.info(f"Using current time: {observation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # Date and time inputs
            selected_date = st.date_input("Date:", datetime.now())
            selected_time = st.time_input("Time:", datetime.now().time())
            
            # Combine date and time
            observation_time = datetime.combine(selected_date, selected_time)
            
        # Advanced options
        st.subheader("Advanced Options")
        show_coords = st.checkbox("Show celestial coordinates (RA/Dec)", value=False)
        above_horizon = st.checkbox("Show only objects above horizon", value=True)
        
    # Return all selected parameters
    return {
        "latitude": latitude,
        "longitude": longitude,
        "elevation": elevation,
        "time": observation_time,
        "show_coords": show_coords,
        "above_horizon": above_horizon
    }


def display_planets_overview(planets_data: List[Dict[str, Any]]):
    """Display overview of all planets"""
    st.header("Planets Overview")
    
    # Format data as DataFrame
    df = format_planet_data_as_df(planets_data)
    
    # Display as table
    st.dataframe(
        df,
        column_config={
            "Name": st.column_config.TextColumn("Name"),
            "Type": st.column_config.TextColumn("Type"),
            "Altitude": st.column_config.TextColumn("Altitude"),
            "Azimuth": st.column_config.TextColumn("Azimuth"),
            "Direction": st.column_config.TextColumn("Direction"),
            "Magnitude": st.column_config.TextColumn("Magnitude"),
            "Constellation": st.column_config.TextColumn("Constellation"),
            "Visible": st.column_config.TextColumn("Visible"),
            "Data Source": st.column_config.TextColumn("Source")
        },
        use_container_width=True
    )
    
    # Count visible celestial bodies
    visible_count = sum(1 for body in planets_data if body.get('altitude', -90) > 0)
    
    st.info(f"Currently {visible_count} out of {len(planets_data)} celestial bodies are above the horizon.")


def display_sky_map(planets_data: List[Dict[str, Any]], params: Dict[str, Any]):
    """Display interactive sky map"""
    st.header("Sky Map")
    
    # Get location and time info
    lat = params["latitude"]
    lon = params["longitude"]
    time_str = params["time"].strftime("%Y-%m-%d %H:%M:%S")
    
    # Create title with location and time
    title = f"Planetary Bodies in the Sky at {time_str}<br>Location: {lat:.4f}°, {lon:.4f}°"
    
    # Add offline mode indicator if needed
    if any(p.get('isSimulated', False) for p in planets_data):
        title += " (Simulated Data)"
    
    # Create and display the map
    fig = create_sky_map(planets_data, title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Add explanation
    st.markdown("""
    **How to read this map:**
    - The sky map shows the view looking up at the sky from your location
    - The edge of the circle represents the horizon in all directions
    - The center of the circle represents the point directly overhead (zenith)
    - North (N), East (E), South (S), and West (W) directions are marked
    - Planets are shown with their name and relative brightness (larger dots = brighter objects)
    - Hover over a planet to see detailed information
    """)


def display_planet_details(planets_data: List[Dict[str, Any]], params: Dict[str, Any]):
    """Display detailed information about a specific planet"""
    st.header("Planet Details")
    
    # Create dropdown to select a planet
    planet_names = [planet['name'] for planet in planets_data]
    selected_planet_name = st.selectbox("Select a planet:", planet_names)
    
    # Get the selected planet data
    selected_planet = next((planet for planet in planets_data if planet['name'] == selected_planet_name), None)
    
    if selected_planet:
        # Create columns for layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Display basic information
            st.subheader(f"{selected_planet_name} Information")
            
            # Extract data
            altitude = selected_planet.get('altitude')
            azimuth = selected_planet.get('azimuth')
            magnitude = selected_planet.get('magnitude')
            constellation = selected_planet.get('constellation', 'Unknown')
            is_simulated = selected_planet.get('isSimulated', False)
            
            # Determine visibility
            visible = altitude is not None and altitude > 0
            visibility_status = "Visible" if visible else "Not visible (below horizon)"
            
            # Create info table
            info_data = {
                "Property": ["Status", "Altitude", "Azimuth", "Direction", "Magnitude", "Constellation", "Data Source"],
                "Value": [
                    visibility_status,
                    f"{altitude:.2f}°" if altitude is not None else "N/A",
                    f"{azimuth:.2f}°" if azimuth is not None else "N/A",
                    astronomy_utils.get_azimuth_direction(azimuth) if azimuth is not None else "N/A",
                    f"{magnitude:.2f}" if magnitude is not None else "N/A",
                    constellation,
                    "Simulated" if is_simulated else "API"
                ]
            }
            
            # Show info as a table
            st.table(pd.DataFrame(info_data))
            
            # Show celestial coordinates if requested
            if params["show_coords"] and "rightAscension" in selected_planet and "declination" in selected_planet:
                ra = selected_planet["rightAscension"]
                dec = selected_planet["declination"]
                
                st.subheader("Celestial Coordinates")
                
                coords_data = {
                    "Coordinate": ["Right Ascension", "Declination"],
                    "Value": [
                        f"{ra['hours']}h {ra['minutes']}m {ra['seconds']:.2f}s",
                        f"{dec['degrees']}° {dec['arcminutes']}' {dec['arcseconds']:.2f}\""
                    ]
                }
                
                st.table(pd.DataFrame(coords_data))
        
        with col2:
            # Display position description
            st.subheader("Where to Look")
            
            if visible:
                # Get user-friendly position description
                position_desc = get_planet_position_info(selected_planet)
                st.success(position_desc)
                
                # Add observation tips
                if magnitude is not None:
                    if magnitude < 0:
                        st.info(f"With a magnitude of {magnitude:.2f}, {selected_planet_name} is very bright and easy to spot.")
                    elif magnitude < 3:
                        st.info(f"With a magnitude of {magnitude:.2f}, {selected_planet_name} should be visible to the naked eye even in urban areas.")
                    elif magnitude < 6:
                        st.info(f"With a magnitude of {magnitude:.2f}, {selected_planet_name} should be visible to the naked eye in dark areas, but may be difficult to see in urban areas.")
                    else:
                        st.info(f"With a magnitude of {magnitude:.2f}, {selected_planet_name} may require binoculars or a telescope to be seen.")
            else:
                st.error(f"{selected_planet_name} is currently below the horizon and not visible from your location.")
                
                # Calculate when it will rise (if possible)
                try:
                    # This would require additional functionality to calculate rise time
                    # For now, just provide a generic message
                    st.info("Try changing your observation time to see when this planet will be visible.")
                except Exception as e:
                    st.warning("Unable to calculate visibility times.")
    else:
        st.error("Planet data not available.")


def create_neo_sky_map(neo_data: List[Dict[str, Any]], title: str = "Near Earth Objects in the Sky") -> go.Figure:
    """
    Create a sky map showing the positions of Near Earth Objects
    
    Args:
        neo_data: List of NEO data with visibility information
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    # Create polar chart
    fig = go.Figure()
    
    # Add horizon circle (altitude = 0 degrees)
    theta = np.linspace(0, 2*np.pi, 100)
    r = np.ones(100) * 90  # Horizon corresponds to zenith distance of 90 degrees
    fig.add_trace(go.Scatterpolar(
        r=r,
        theta=np.degrees(theta),
        mode='lines',
        line=dict(color='gray', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add altitude degree circles (30 and 60 degrees)
    for altitude in [30, 60]:
        r = np.ones(100) * (90 - altitude)
        fig.add_trace(go.Scatterpolar(
            r=r,
            theta=np.degrees(theta),
            mode='lines',
            line=dict(color='lightgray', width=0.5, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add direction markers (N, E, S, W)
    directions = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
    for direction, angle in directions.items():
        fig.add_trace(go.Scatterpolar(
            r=[95],  # Slightly beyond the horizon
            theta=[angle],
            mode='text',
            text=[direction],
            textfont=dict(size=12, color='black'),
            showlegend=False
        ))
    
    # Add NEOs
    for neo in neo_data:
        # Extract data
        name = neo.get('name', 'Unknown')
        elevation = neo.get('elevation')
        azimuth = neo.get('azimuth')
        
        # Skip NEOs without position data
        if elevation is None or azimuth is None:
            continue
        
        # Calculate zenith distance (90 degrees - altitude)
        zenith_distance = 90 - elevation
        
        # Determine point size (based on diameter, larger NEOs = larger points)
        diameter = neo.get('diameter_avg_km', 0)
        size = max(8, min(20, 8 + diameter * 10))  # Scale size based on diameter
        
        # Determine point color (potentially hazardous = red, otherwise orange)
        color = "#ff0000" if neo.get("is_potentially_hazardous") else "#ff8c00"
        
        # Add NEO point
        fig.add_trace(go.Scatterpolar(
            r=[zenith_distance],
            theta=[azimuth],
            mode='markers+text',
            marker=dict(size=size, color=color, symbol='diamond'),
            text=[name],
            textposition="top center",
            name=name,
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Type: Near Earth Object<br>"
                f"Altitude: {elevation:.1f}°<br>"
                f"Azimuth: {azimuth:.1f}°<br>"
                f"Diameter: {neo.get('diameter_avg_km', 0):.2f} km<br>"
                f"Distance: {neo.get('miss_distance_km', 0):,.0f} km<br>"
                f"Hazardous: {'Yes' if neo.get('is_potentially_hazardous') else 'No'}"
            ),
            customdata=[[elevation, azimuth, neo.get('diameter_avg_km', 0)]],
            showlegend=True
        ))
    
    # Set chart layout
    fig.update_layout(
        title=dict(text=title, x=0.5),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 90],
                tickmode='array',
                tickvals=[0, 30, 60, 90],
                ticktext=['90°', '60°', '30°', '0°'],
                tickfont=dict(size=10),
                tickangle=0,
            ),
            angularaxis=dict(
                visible=True,
                tickmode='array',
                tickvals=[0, 90, 180, 270],
                ticktext=['N', 'E', 'S', 'W'],
                direction="clockwise",
            ),
            bgcolor='aliceblue',
        ),
        showlegend=True,
        legend=dict(
            title="Near Earth Objects",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def display_neo_sky_map(selected_neos: List[Dict[str, Any]], params: Dict[str, Any]):
    """Display sky map with selected Near Earth Objects"""
    st.header("NEO Sky Map")
    
    # Get location and time info
    lat = params["latitude"]
    lon = params["longitude"]
    time_str = params["time"].strftime("%Y-%m-%d %H:%M:%S")
    
    # Create title with location and time
    title = f"Near Earth Objects in the Sky at {time_str}<br>Location: {lat:.4f}°, {lon:.4f}°"
    
    # Create and display the map
    fig = create_neo_sky_map(selected_neos, title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Add explanation
    st.markdown("""
    **How to read this map:**
    - The sky map shows the approximate positions of selected Near Earth Objects
    - The edge of the circle represents the horizon in all directions
    - The center of the circle represents the point directly overhead (zenith)
    - North (N), East (E), South (S), and West (W) directions are marked
    - Red diamonds indicate potentially hazardous objects, orange diamonds are non-hazardous
    - Size of the diamond indicates the relative size of the object
    - All NEOs flying over your location are shown, regardless of their size or distance
    - Many smaller or distant NEOs would not be visible to the naked eye, but are still mapped
    
    **Note:** The positions shown are approximations based on limited data. For precise astronomical observations, please consult specialized resources.
    """)


def display_additional_info(params: Dict[str, Any], planets_data: List[Dict[str, Any]]):
    """Display additional astronomical information"""
    st.header("Additional Astronomical Information")
    
    # Check if we're using simulated data
    using_simulated_data = any(planet.get('isSimulated', False) for planet in planets_data)
    
    # Create tabs for different types of information
    tab1, tab2 = st.tabs(["Moon Phase", "Twilight Times"])
    
    with tab1:
        # Display moon phase information
        st.subheader("Moon Phase")
        
        try:
            # Get moon phase information
            moon_phase = planets_api.get_moon_phase(params["time"])
            
            # Display moon phase information
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Phase", f"{moon_phase['phase_name']}")
                st.metric("Illumination", f"{moon_phase['phase_percent']}%")
            with col2:
                st.metric("Distance", f"{moon_phase['distance_km']:,} km")
                st.metric("Angular Diameter", f"{moon_phase['angular_diameter_degrees']}°")
        except Exception as e:
            st.error(f"Error retrieving moon phase: {str(e)}")
            st.info("Moon phase information could not be retrieved. Please try again later.")
        
    with tab2:
        # Display twilight times
        st.subheader("Twilight Times")
        
        try:
            # Get twilight times
            twilight_times = planets_api.get_twilight_times(
                latitude=params["latitude"],
                longitude=params["longitude"],
                date_obj=params["time"],
                twilight_type='civil'
            )
            
            # Display twilight times
            if 'dawn' in twilight_times and 'dusk' in twilight_times:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Dawn", twilight_times['dawn'])
                with col2:
                    st.metric("Dusk", twilight_times['dusk'])
            else:
                st.info("Twilight times could not be calculated for this location and time.")
        except Exception as e:
            st.error(f"Error retrieving twilight times: {str(e)}")
            st.info("Twilight times could not be retrieved. Please try again later.")


def display_neo_page(params):
    """Display Near Earth Objects page"""
    st.header("Near Earth Objects Tracker")
    
    st.markdown("""
    This page allows you to track Near Earth Objects (NEOs) such as asteroids that come close to Earth.
    You can see which NEOs are currently visible in the sky based on your location.
    
    Data is provided by NASA's Near Earth Object Web Service (NeoWs).
    """)
    
    # Import neo_api here to avoid circular imports
    import neo_api
    
    # Initialize session state for NEO data and selected NEOs
    if "neo_data_cache" not in st.session_state:
        st.session_state.neo_data_cache = None
        st.session_state.visible_neos = None
        st.session_state.selected_neo_ids = set()
    
    # Date selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now().date())
    with col2:
        end_date = st.date_input("End Date", (datetime.now() + timedelta(days=7)).date())
    
    # NASA API key input (optional)
    api_key = st.text_input("NASA API Key (optional, leave blank to use DEMO_KEY)", "", type="password")
    if not api_key:
        api_key = "DEMO_KEY"
        st.info("Using DEMO_KEY. This has rate limits of 30 requests per hour and 50 requests per day. Consider getting your own API key from api.nasa.gov for higher limits.")
    
    # Query button
    fetch_button = st.button("Find Near Earth Objects")
    
    # Use cached data if available and button not pressed
    if fetch_button:
        with st.spinner("Fetching NEO data..."):
            try:
                # Format dates as strings (YYYY-MM-DD)
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                # Get NEO data
                neo_data = neo_api.get_neo_feed(start_date_str, end_date_str, api_key)
                
                # Store in session state
                st.session_state.neo_data_cache = neo_data
                st.session_state.visible_neos = None  # Reset visible NEOs
                
                if not neo_data:
                    st.warning("No Near Earth Objects found for the selected date range.")
                    return
                
                # Display NEO count
                st.success(f"Found {len(neo_data)} Near Earth Objects between {start_date_str} and {end_date_str}")
                
                # Display NEO list
                display_neo_list(neo_data, params)
            except Exception as e:
                st.error(f"Error fetching NEO data: {str(e)}")
                st.info("This might be due to API rate limits or network issues. Please try again later or use a different API key.")
    # Use cached data if available and button not pressed
    elif st.session_state.neo_data_cache is not None:
        neo_data = st.session_state.neo_data_cache
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Display NEO count
        st.success(f"Found {len(neo_data)} Near Earth Objects between {start_date_str} and {end_date_str}")
        
        # Display NEO list
        display_neo_list(neo_data, params)


def display_neo_list(neo_data, params):
    """Display list of Near Earth Objects"""
    st.subheader("Near Earth Objects List")
    
    # Sort NEOs by close approach date
    sorted_neos = sorted(neo_data, key=lambda x: x.get("close_approach_date", ""))
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Table View", "Detailed View", "Sky Map"])
    
    with tab1:
        # Create DataFrame for table view
        df = pd.DataFrame([
            {
                "Name": neo.get("name"),
                "Date": neo.get("close_approach_date"),
                "Diameter (km)": f"{neo.get('diameter_avg_km', 0):.2f}",
                "Distance (km)": f"{neo.get('miss_distance_km', 0):,.0f}",
                "Distance (lunar)": f"{neo.get('miss_distance_lunar', 0):.1f}",
                "Velocity (km/h)": f"{neo.get('velocity_km_per_hour', 0):,.0f}",
                "Hazardous": "Yes" if neo.get("is_potentially_hazardous") else "No"
            }
            for neo in sorted_neos
        ])
        
        st.dataframe(df)
    
    with tab2:
        # For each NEO, create an expandable section with details
        for neo in sorted_neos:
            with st.expander(f"{neo.get('name')} - {neo.get('close_approach_date')}"):
                # Display basic info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**ID:** {neo.get('id')}")
                    st.markdown(f"**Name:** {neo.get('name')}")
                    st.markdown(f"**Approach Date:** {neo.get('close_approach_date')}")
                    st.markdown(f"**Orbiting Body:** {neo.get('orbiting_body', 'Earth')}")
                
                with col2:
                    st.markdown(f"**Diameter:** {neo.get('diameter_min_km', 0):.2f} - {neo.get('diameter_max_km', 0):.2f} km")
                    st.markdown(f"**Miss Distance:** {neo.get('miss_distance_km', 0):,.0f} km ({neo.get('miss_distance_lunar', 0):.1f} lunar distances)")
                    st.markdown(f"**Velocity:** {neo.get('velocity_km_per_hour', 0):,.0f} km/h")
                    st.markdown(f"**Potentially Hazardous:** {'Yes' if neo.get('is_potentially_hazardous') else 'No'}")
                
                # Add link to NASA JPL page
                if neo.get("nasa_jpl_url"):
                    st.markdown(f"[View on NASA JPL website]({neo.get('nasa_jpl_url')})")
                
                # Calculate and display visibility information
                st.subheader("Visibility Information")
                
                # Get visibility information
                import neo_api
                visibility_info = neo_api.get_neo_visibility(
                    neo, 
                    latitude=params["latitude"],
                    longitude=params["longitude"]
                )
                
                if visibility_info["visible"]:
                    st.success(f"This NEO may be visible in the {visibility_info['direction']} direction at approximately {visibility_info['elevation']}° above the horizon.")
                    st.info(visibility_info["note"])
                else:
                    st.warning(f"This NEO is not currently visible from your location: {visibility_info['reason']}")
    
    with tab3:
        st.subheader("NEOs Sky Map")
        
        # Initialize session state for NEO data if not exists
        if "neo_data_cache" not in st.session_state:
            st.session_state.neo_data_cache = None
            st.session_state.visible_neos = None
            st.session_state.selected_neo_ids = set()
        
        # Cache the current NEO data to prevent recalculation
        st.session_state.neo_data_cache = sorted_neos
        
        # Get potentially visible NEOs (only calculate if not already in session state)
        if st.session_state.visible_neos is None:
            visible_neos = []
            for neo in sorted_neos:
                # Get visibility information
                import neo_api
                visibility_info = neo_api.get_neo_visibility(
                    neo, 
                    latitude=params["latitude"],
                    longitude=params["longitude"]
                )
                
                # Add visibility info to NEO data
                if visibility_info["visible"]:
                    neo_with_visibility = neo.copy()
                    neo_with_visibility.update(visibility_info)
                    visible_neos.append(neo_with_visibility)
            
            # Cache the visible NEOs
            st.session_state.visible_neos = visible_neos
        else:
            # Use cached visible NEOs
            visible_neos = st.session_state.visible_neos
        
        if not visible_neos:
            st.info("None of the Near Earth Objects are estimated to be flying over your location.")
        else:
            st.write(f"The following {len(visible_neos)} NEOs are calculated to fly over your location (note that some may be too small to see with the naked eye):")
            
            # Create checkboxes for each visible NEO and track selections in session state
            selected_neos = []
            for neo in visible_neos:
                neo_id = neo.get('id')
                checkbox_key = f"neo_map_{neo_id}"
                
                # Check if this NEO is selected
                if st.checkbox(
                    f"{neo.get('name')} - {neo.get('close_approach_date')} - {neo.get('direction')} direction", 
                    key=checkbox_key,
                    value=neo_id in st.session_state.selected_neo_ids  # Pre-select based on session state
                ):
                    selected_neos.append(neo)
                    st.session_state.selected_neo_ids.add(neo_id)  # Add to selected set
                elif neo_id in st.session_state.selected_neo_ids:
                    st.session_state.selected_neo_ids.remove(neo_id)  # Remove from selected set
            
            # Display sky map if any NEOs are selected
            if selected_neos:
                display_neo_sky_map(selected_neos, params)
            else:
                st.info("Select one or more NEOs above to display them on the sky map.")


def main():
    """Main application function"""
    # Set page configuration
    st.set_page_config(
        page_title="Celestial Body Tracker",
        page_icon="🪐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Display header
    app_header()
    
    # Get location and time parameters from sidebar
    params = location_time_sidebar()
    
    # Add page selection in sidebar
    st.sidebar.header("Page Selection")
    page = st.sidebar.radio(
        "Select Page:",
        ["Planets & Moons", "3D Solar System", "Near Earth Objects"]
    )
    
    try:
        if page == "Planets & Moons":
            # Original planets page
            with st.spinner("Fetching planet data..."):
                planets_data = planets_api.get_visible_planets(
                    latitude=params["latitude"],
                    longitude=params["longitude"],
                    elevation=params["elevation"],
                    time=params["time"],
                    show_coords=params["show_coords"],
                    above_horizon=params["above_horizon"],
                    use_offline_mode=False
                )
            
            # Display calculation info
            display_calculation_info()
            
            # Display planets overview
            display_planets_overview(planets_data)
            
            # Display sky map
            display_sky_map(planets_data, params)
            
            # Display planet details
            display_planet_details(planets_data, params)
            
            # Display additional information
            display_additional_info(params, planets_data)
            
        elif page == "3D Solar System":
            # 3D Solar System visualization
            solar_system_3d.show_3d_solar_system()
            
        elif page == "Near Earth Objects":
            # New NEO page
            display_neo_page(params)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("""
        An error occurred while calculating planetary positions. This might be due to issues with the Skyfield library or data files.
        
        Please check the error message above and try again.
        """)


if __name__ == "__main__":
    main()
