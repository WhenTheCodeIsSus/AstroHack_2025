# Celestial Bodies Tracker

## A comprehensive application for tracking planets, moons, and other celestial bodies in real-time

This application provides real-time tracking and visualization of celestial bodies in the sky based on observer location and time. Powered by the [Skyfield](https://rhodesmill.org/skyfield/) astronomical library, it offers detailed information about planets, dwarf planets, and various moons in our solar system.

## Features

- **Real-time celestial body tracking**: View positions of planets, moons, and other celestial bodies
- **Interactive sky map**: Visual representation of celestial bodies with altitude and azimuth
- **3D Solar System visualization**: Explore the solar system in three dimensions with interactive controls
- **Detailed information**: Altitude, azimuth, magnitude, constellation, and more for each body
- **Observer customization**: Set your location (latitude, longitude, elevation) and observation time
- **Visibility calculation**: Determine if celestial bodies are visible from your location
- **Moon phase information**: Track lunar phases and illumination percentage
- **Near Earth Object (NEO) tracking**: Information about asteroids and other objects approaching Earth
- **Offline functionality**: Works without internet connection using local calculations

## Installation Requirements

```bash
# Install required Python packages
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
streamlit run app.py
```

## API Usage

NASA Near Earth Object API


## Supported Celestial Bodies

The application tracks a wide variety of celestial bodies:

### Solar System Bodies
- **Sun**: Our star
- **Planets**: Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
- **Dwarf Planets**: Pluto

### Natural Satellites
- **Earth's Moon**
- **Jupiter's Galilean Moons**: Io, Europa, Ganymede, Callisto
- **Saturn's Major Moons**: Titan, Enceladus, Mimas, Dione, Rhea, Iapetus
- **Uranus's Major Moons**: Miranda, Ariel, Umbriel, Titania, Oberon
- **Neptune's Major Moons**: Triton, Nereid

Each celestial body is color-coded and sized according to its type and brightness in the sky map display.

## Query Parameters

| Parameter | Default Value | Description | Minimum Version Compatible |
| --------- | ------------- | ----------- | -------------------------- |
| latitude | 28.627222 | Latitude of observer | v1 |
| longitude | -80.620833 | Longitude of observer | v1 |
| elevation | 0 | Elevation of observer in meters above sea level | v1 |
| time | null | Time of observation in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format, defaults to time of request | v2 |
| showCoords | false | Display declination and right ascension of each body, expects true or false | v2 |
| aboveHorizon | true | Set to false to display all celestial bodies even if they are below the horizon | v2 |

## Project Structure

- `app.py` - Main application file
- `astronomy_utils.py` - Astronomical calculation utilities
- `planets_api.py` - Planetary body API module
- `neo_api.py` - Near Earth Object API module
- `solar_system_3d.py` - 3D Solar System visualization module

## Technical Details

## Astronomy Calculations
- **Skyfield library**: Used for high-precision astronomical calculations
- **Astropy**: Used for celestial coordinate conversions and constellation identification
- **Caching mechanism**: Implemented to improve performance of repeated calculations

## Visualization
- **Plotly**: Used for interactive sky map and 3D visualization
- **Matplotlib**: Used for additional visualizations
- **Streamlit**: Used for the web application interface

## Contributing

Contributions to improve the application are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Skyfield](https://rhodesmill.org/skyfield/) for astronomical calculations
- [Streamlit](https://streamlit.io/) for the web application framework
- [Astropy](https://www.astropy.org/) for astronomical tools and resources
