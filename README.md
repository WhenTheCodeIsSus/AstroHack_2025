# Celestial Bodies Tracker

## A comprehensive application for tracking planets, moons, and other celestial bodies in real-time

This application provides real-time tracking and visualization of celestial bodies in the sky based on observer location and time. Powered by the [Skyfield](https://rhodesmill.org/skyfield/) astronomical library, it offers detailed information about planets, dwarf planets, and various moons in our solar system.

## Features

- **Real-time celestial body tracking**: View positions of planets, moons, and other celestial bodies
- **Interactive sky map**: Visual representation of celestial bodies with altitude and azimuth
- **Detailed information**: Altitude, azimuth, magnitude, constellation, and more for each body
- **Observer customization**: Set your location (latitude, longitude, elevation) and observation time
- **Visibility calculation**: Determine if celestial bodies are visible from your location
- **Moon phase information**: Track lunar phases and illumination percentage
- **Near Earth Object (NEO) tracking**: Information about asteroids and other objects approaching Earth
- **Offline functionality**: Works without internet connection using local calculations

## Available Versions

The application is available in two versions:

1. **Standard version** (English): Original implementation with comprehensive functionality
2. **Optimized version** (Chinese): Enhanced performance, additional features, and Chinese localization

## Installation Requirements

```bash
# Install required Python packages
pip install streamlit pandas numpy matplotlib plotly skyfield astropy pytz requests
```

## Usage

```bash
# Run the standard version (English)
streamlit run app.py

# Run the optimized version (Chinese)
streamlit run app_optimized.py

# Run tests for the optimized version
python test_optimized.py
```

## API Usage

Get a list of planets (and Moon) above the horizon:
```
GET https://api.visibleplanets.dev/v3?latitude=32&longitude=-98
```

Get a list of planets (and Moon) with their declination and right ascension coordinates:
```
GET https://api.visibleplanets.dev/v3?latitude=32&longitude=-98&showCoords=true
```

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

- `app.py` - Main application file (English version)
- `app_optimized.py` - Optimized application file (Chinese version)
- `astronomy_utils.py` - Astronomical calculation utilities (English version)
- `astronomy_utils_optimized.py` - Optimized astronomical calculation utilities (Chinese version)
- `planets_api.py` - Planetary body API module
- `neo_api.py` - Near Earth Object API module
- `test_optimized.py` - Test script for optimized modules

## Technical Details

### Astronomy Calculations
- **Skyfield library**: Used for high-precision astronomical calculations
- **Astropy**: Used for celestial coordinate conversions and constellation identification
- **Caching mechanism**: Implemented to improve performance of repeated calculations

### Visualization
- **Plotly**: Used for interactive sky map visualization
- **Matplotlib**: Used for additional visualizations
- **Streamlit**: Used for the web application interface

### Optimizations (in the optimized version)
- **Improved caching**: Enhanced caching strategy for better performance
- **Preloaded ephemeris data**: Loads astronomical data once at startup
- **Chinese localization**: User interface and descriptions translated to Chinese
- **Additional celestial bodies**: Support for more moons and improved categorization

## Changelog

### 2025-07-03
#### v4.1
- Added support for many more natural satellites:
  - Saturn's additional moons: Mimas, Dione, Rhea, and Iapetus
  - Uranus's major moons: Miranda, Ariel, Umbriel, Titania, and Oberon
  - Neptune's moons: Triton and Nereid
- Enhanced visualization with distinctive symbols for moons of different planets
- Adjusted size scaling to better represent relative importance and visibility of various moons
- Improved categorization of celestial bodies in the sky map

#### v4.0
- Added support for additional celestial bodies including Pluto, Jupiter's Galilean moons (Io, Europa, Ganymede, Callisto), and Saturn's major moons (Titan, Enceladus)
- Improved visualization with different symbols and sizes for different types of celestial bodies
- Added celestial body type classification in the planets overview table
- Enhanced hover information in the sky map to show body type
- Fixed timezone handling in date/time calculations
- Corrected API connection issues

### 2022-11-28
- Moved the public API to fly.io with Heroku sunsetting their hobby plans
- Fixed a crash caused by new celestial bodies added to latest Astronomy Engine
- Updated default coordinates to Launchpad 39-B at NASA's Kennedy Space Center

### 2022-10-08
#### v3
- Now uses [Don Cross' Astronomy Engine](https://www.npmjs.com/package/astronomy-engine) published on NPM
- The active Astronomy Engine version is provided in the response meta object as `engineVersion`
- Added the `aboveHorizon` request param to filter bodies that are above the horizon only
- Each body now includes visual `magnitude`, `altitude`, `azimuth`, and `constellation`
- Right ascension and declination hours/degrees will no longer display negative values

#### v2
- Added query parameter to set time of observation using ISO 8601 format
- Added the `aboveHorizon` param to filter bodies above the horizon
- Changed declination response properties from hours to degrees, minutes to arcminutes, seconds to arcseconds
- Changed declination and right ascension response values from strings to numbers
- Fixed typo in `rightAscension` response parameter
- Response now follows JSON:API spec and includes parameters used to generate sky

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
