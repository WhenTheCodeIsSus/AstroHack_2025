#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
3D Solar System Visualization Module

This module provides functionality to visualize the solar system in 3D using Plotly.
It uses the Skyfield library to calculate the 3D positions of planets and other celestial bodies.

Main features:
    - 3D visualization of planets, dwarf planets, and moons
    - Interactive controls for rotating, zooming, and exploring the solar system
    - Time-based position calculations showing celestial bodies at specific dates/times
    - Customizable display options

Usage:
    Import this module and call the show_3d_solar_system() function in your Streamlit app
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
import math

# Import custom modules
import planets_api
from planets_api import ts, ephemeris, PLANETS
from app import PLANET_COLORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for visualization
SUN_SIZE = 20  # Visual size of the Sun in the 3D plot
PLANET_SIZE_SCALE = {
    'Mercury': 3.8,
    'Venus': 9.5,
    'Earth': 10.0,
    'Mars': 5.3,
    'Jupiter': 112.0,
    'Saturn': 94.5,
    'Uranus': 40.0,
    'Neptune': 38.8,
    'Pluto': 1.8,
    'Moon': 2.7,
    'Sun': 109.0
}

# Scale factors for better visualization
# Real sizes would make planets nearly invisible
SIZE_MULTIPLIER = 0.5
MOON_SIZE_MULTIPLIER = 0.8

def get_planets_3d_coordinates(time=None):
    """
    Get 3D coordinates of planets in the solar system
    
    Args:
        time: Observation time, defaults to current time
        
    Returns:
        Dictionary mapping planet names to their 3D coordinates in AU
    """
    # Use current time if not provided
    if time is None:
        time = datetime.now(tz=pytz.utc)
    elif time.tzinfo is None:
        time = time.replace(tzinfo=pytz.utc)
    
    # Convert datetime to Skyfield time
    t = ts.from_datetime(time)
    
    # Calculate 3D positions for all planets
    planets_3d = {}
    
    # Add Sun at the center
    planets_3d['Sun'] = {
        'x': 0,
        'y': 0,
        'z': 0,
        'name': 'Sun',
        'color': PLANET_COLORS.get('Sun', '#ffff00'),
        'size': SUN_SIZE,
        'type': 'star'
    }
    
    for name, planet in PLANETS.items():
        try:
            # Skip Sun as we've already added it at the center
            if name == 'Sun':
                continue
                
            # Get heliocentric (sun-centered) position in AU
            position = planet.at(t).position.au
            
            # Determine body type
            body_type = 'planet'
            if name in ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']:
                body_type = 'planet'
            elif name == 'Pluto':
                body_type = 'dwarf_planet'
            elif name == 'Moon':
                body_type = 'moon'
            elif name in ['Io', 'Europa', 'Ganymede', 'Callisto']:
                body_type = 'jupiter_moon'
            elif name in ['Titan', 'Enceladus', 'Mimas', 'Dione', 'Rhea', 'Iapetus']:
                body_type = 'saturn_moon'
            elif name in ['Miranda', 'Ariel', 'Umbriel', 'Titania', 'Oberon']:
                body_type = 'uranus_moon'
            elif name in ['Triton', 'Nereid']:
                body_type = 'neptune_moon'
            
            # Calculate visual size based on planet type and relative size
            base_size = PLANET_SIZE_SCALE.get(name, 5.0)
            if body_type == 'planet':
                size = base_size * SIZE_MULTIPLIER
            elif body_type == 'dwarf_planet':
                size = 3 * SIZE_MULTIPLIER
            elif body_type.endswith('_moon'):
                size = 2 * MOON_SIZE_MULTIPLIER
            else:
                size = 3 * SIZE_MULTIPLIER
            
            # Store x, y, z coordinates and metadata
            planets_3d[name] = {
                'x': float(position[0]),
                'y': float(position[1]),
                'z': float(position[2]),
                'name': name,
                'color': PLANET_COLORS.get(name, '#808080'),
                'size': size,
                'type': body_type
            }
            
        except Exception as e:
            logger.warning(f"Error calculating 3D position for {name}: {str(e)}")
    
    return planets_3d

def add_orbit_paths(fig, time=None):
    """
    Add orbit paths for planets
    
    Args:
        fig: Plotly figure object to add orbits to
        time: Base time for orbit calculation
        
    Returns:
        Updated Plotly figure with orbit paths
    """
    if time is None:
        time = datetime.now(tz=pytz.utc)
    
    # Main planets to show orbits for
    orbit_planets = ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    
    for planet_name in orbit_planets:
        if planet_name not in PLANETS:
            continue
            
        planet = PLANETS[planet_name]
        
        # Calculate positions at multiple points around the orbit
        orbit_points = 100
        orbit_x = []
        orbit_y = []
        orbit_z = []
        
        for i in range(orbit_points):
            # Calculate time offset based on orbital period
            # This is a simplified approach - actual orbits would require more complex calculations
            days_offset = i * 365 / orbit_points  # Adjust based on planet
            if planet_name == 'Mercury':
                days_offset = i * 88 / orbit_points
            elif planet_name == 'Venus':
                days_offset = i * 225 / orbit_points
            elif planet_name == 'Mars':
                days_offset = i * 687 / orbit_points
            elif planet_name == 'Jupiter':
                days_offset = i * 4333 / orbit_points
            elif planet_name == 'Saturn':
                days_offset = i * 10759 / orbit_points
            elif planet_name == 'Uranus':
                days_offset = i * 30687 / orbit_points
            elif planet_name == 'Neptune':
                days_offset = i * 60190 / orbit_points
            
            time_point = time + timedelta(days=days_offset)
            t = ts.from_datetime(time_point)
            
            try:
                position = planet.at(t).position.au
                orbit_x.append(float(position[0]))
                orbit_y.append(float(position[1]))
                orbit_z.append(float(position[2]))
            except Exception as e:
                logger.warning(f"Error calculating orbit point for {planet_name}: {str(e)}")
        
        # Add orbit path to figure
        if orbit_x:
            color = PLANET_COLORS.get(planet_name, '#808080')
            fig.add_trace(go.Scatter3d(
                x=orbit_x,
                y=orbit_y,
                z=orbit_z,
                mode='lines',
                line=dict(color=color, width=1),
                opacity=0.5,
                name=f"{planet_name} Orbit",
                showlegend=False
            ))
    
    return fig

@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_solar_system_3d(planets_3d, show_orbits=True, title="Solar System 3D View"):
    """
    Create a 3D visualization of the solar system
    
    Args:
        planets_3d: Dictionary mapping planet names to their 3D coordinates
        show_orbits: Whether to show orbit paths
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Group celestial bodies by type for better organization
    stars = []
    planets = []
    dwarf_planets = []
    moons = []
    jupiter_moons = []
    saturn_moons = []
    uranus_moons = []
    neptune_moons = []
    
    for name, data in planets_3d.items():
        body_type = data.get('type', '')
        if body_type == 'star':
            stars.append(data)
        elif body_type == 'planet':
            planets.append(data)
        elif body_type == 'dwarf_planet':
            dwarf_planets.append(data)
        elif body_type == 'moon':
            moons.append(data)
        elif body_type == 'jupiter_moon':
            jupiter_moons.append(data)
        elif body_type == 'saturn_moon':
            saturn_moons.append(data)
        elif body_type == 'uranus_moon':
            uranus_moons.append(data)
        elif body_type == 'neptune_moon':
            neptune_moons.append(data)
    
    # Add the Sun at the center
    if stars:
        sun = stars[0]  # The Sun should be the only star
        fig.add_trace(go.Scatter3d(
            x=[sun['x']],
            y=[sun['y']],
            z=[sun['z']],
            mode='markers',
            marker=dict(
                size=sun['size'],
                color=sun['color'],
                opacity=0.9
            ),
            name=sun['name'],
            text=[sun['name']],
            hovertemplate="<b>%{text}</b><br>The center of our solar system",
        ))
    
    # Add planets
    if planets:
        x = [p['x'] for p in planets]
        y = [p['y'] for p in planets]
        z = [p['z'] for p in planets]
        names = [p['name'] for p in planets]
        colors = [p['color'] for p in planets]
        sizes = [p['size'] for p in planets]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers+text',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name='Planets',
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add dwarf planets
    if dwarf_planets:
        x = [p['x'] for p in dwarf_planets]
        y = [p['y'] for p in dwarf_planets]
        z = [p['z'] for p in dwarf_planets]
        names = [p['name'] for p in dwarf_planets]
        colors = [p['color'] for p in dwarf_planets]
        sizes = [p['size'] for p in dwarf_planets]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers+text',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name='Dwarf Planets',
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add Earth's Moon
    if moons:
        x = [p['x'] for p in moons]
        y = [p['y'] for p in moons]
        z = [p['z'] for p in moons]
        names = [p['name'] for p in moons]
        colors = [p['color'] for p in moons]
        sizes = [p['size'] for p in moons]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name="Earth's Moon",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add Jupiter's moons
    if jupiter_moons:
        x = [p['x'] for p in jupiter_moons]
        y = [p['y'] for p in jupiter_moons]
        z = [p['z'] for p in jupiter_moons]
        names = [p['name'] for p in jupiter_moons]
        colors = [p['color'] for p in jupiter_moons]
        sizes = [p['size'] for p in jupiter_moons]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name="Jupiter's Moons",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add Saturn's moons
    if saturn_moons:
        x = [p['x'] for p in saturn_moons]
        y = [p['y'] for p in saturn_moons]
        z = [p['z'] for p in saturn_moons]
        names = [p['name'] for p in saturn_moons]
        colors = [p['color'] for p in saturn_moons]
        sizes = [p['size'] for p in saturn_moons]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name="Saturn's Moons",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add Uranus's moons
    if uranus_moons:
        x = [p['x'] for p in uranus_moons]
        y = [p['y'] for p in uranus_moons]
        z = [p['z'] for p in uranus_moons]
        names = [p['name'] for p in uranus_moons]
        colors = [p['color'] for p in uranus_moons]
        sizes = [p['size'] for p in uranus_moons]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name="Uranus's Moons",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add Neptune's moons
    if neptune_moons:
        x = [p['x'] for p in neptune_moons]
        y = [p['y'] for p in neptune_moons]
        z = [p['z'] for p in neptune_moons]
        names = [p['name'] for p in neptune_moons]
        colors = [p['color'] for p in neptune_moons]
        sizes = [p['size'] for p in neptune_moons]
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.8
            ),
            text=names,
            name="Neptune's Moons",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x: %{x:.3f} AU<br>"
                "y: %{y:.3f} AU<br>"
                "z: %{z:.3f} AU<br>"
            )
        ))
    
    # Add orbit paths if requested
    if show_orbits:
        # Get the first datetime from any planet data
        current_time = datetime.now(tz=pytz.utc)
        fig = add_orbit_paths(fig, current_time)
    
    # Set layout
    fig.update_layout(
        title=dict(text=title, x=0.5),
        scene=dict(
            xaxis_title='X (AU)',
            yaxis_title='Y (AU)',
            zaxis_title='Z (AU)',
            aspectmode='data'  # Keep the natural aspect ratio
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    return fig

def show_3d_solar_system():
    """
    Display the 3D solar system visualization page
    """
    st.title("3D Solar System Visualization")
    
    # Add a description
    st.markdown("""
    This 3D visualization shows the positions of planets and other celestial bodies in our solar system.
    Use your mouse to rotate, zoom, and explore the solar system in three dimensions.
    """)
    
    # Add display options in sidebar
    st.sidebar.header("Display Options")
    
    # Add time selection
    st.sidebar.subheader("Time Settings")
    selected_date = st.sidebar.date_input("Select date", datetime.now())
    selected_time = st.sidebar.time_input("Select time", datetime.now().time())
    
    # Combine date and time
    selected_datetime = datetime.combine(selected_date, selected_time)
    selected_datetime = pytz.utc.localize(selected_datetime)
    
    # Add visualization options
    st.sidebar.subheader("Visualization Options")
    show_orbits = st.sidebar.checkbox("Show planet orbits", value=True)
    
    # Filter options
    st.sidebar.subheader("Filter Celestial Bodies")
    show_planets = st.sidebar.checkbox("Show planets", value=True)
    show_moons = st.sidebar.checkbox("Show moons", value=True)
    show_dwarf_planets = st.sidebar.checkbox("Show dwarf planets", value=True)
    
    # Get 3D coordinates
    planets_3d = get_planets_3d_coordinates(selected_datetime)
    
    # Apply filters
    filtered_planets_3d = {}
    for name, data in planets_3d.items():
        body_type = data.get('type', '')
        
        # Always include the Sun
        if name == 'Sun':
            filtered_planets_3d[name] = data
            continue
            
        # Apply filters
        if body_type == 'planet' and not show_planets:
            continue
        if body_type == 'dwarf_planet' and not show_dwarf_planets:
            continue
        if ('moon' in body_type or body_type == 'moon') and not show_moons:
            continue
            
        filtered_planets_3d[name] = data
    
    # Create 3D visualization
    fig = create_solar_system_3d(filtered_planets_3d, show_orbits)
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
    # Add some additional information
    with st.expander("About this visualization"):
        st.markdown("""
        This visualization shows the positions of planets and other celestial bodies in our solar system.
        The coordinates are heliocentric (Sun-centered) and measured in Astronomical Units (AU).
        1 AU is the average distance from Earth to the Sun, approximately 150 million kilometers.
        
        The visualization is interactive. You can:
        - Rotate: Click and drag
        - Zoom: Scroll or pinch
        - Pan: Right-click and drag
        - Reset view: Double-click
        
        Note: The sizes of celestial bodies are not to scale. In reality, the Sun is much larger and
        the planets are much smaller relative to the distances between them. The sizes have been
        adjusted for better visualization.
        """)
        
        # Show current time
        st.write(f"Current visualization time: {selected_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")

if __name__ == "__main__":
    show_3d_solar_system()
