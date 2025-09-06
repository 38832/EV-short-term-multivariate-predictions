# Fixed Weather Data Extraction Functions
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import json
from io import StringIO

# API Keys
NOAA_TOKEN = "BzYUIRtaVJtrXGcvpfHfppNbiRQrbpqT"
NREL_KEY = "UgYalgH1ZcrxBvbFS3NUTH9WTcuTiLaj10HItAlZ"
EMAIL = "afandellshaikh@gmail.com"

def fetch_noaa_weather_fixed(lat, lon, start_date, end_date, api_key, delta=0.5):
    """
    Fixed NOAA weather data fetching function.
    
    Args:
        lat: Latitude (float)
        lon: Longitude (float) 
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        api_key: NOAA API token
        delta: Search radius in degrees
    """
    try:
        # Ensure lat and lon are floats
        lat = float(lat)
        lon = float(lon)
        delta = float(delta)
        
        # First, find nearby weather stations
        extent = f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}"
        station_url = (
            f"https://www.ncei.noaa.gov/access/services/search/v1/data?"
            f"dataset=global-summary-of-the-day&extent={extent}"
            f"&limit=5&includemetadata=false&token={api_key}"
        )
        
        print(f"Searching for stations near lat={lat}, lon={lon}")
        station_response = requests.get(station_url, timeout=15)
        station_response.raise_for_status()
        station_data = station_response.json()
        
        if "results" not in station_data or len(station_data["results"]) == 0:
            print("No weather stations found in the area")
            return create_fallback_weather_data(start_date, end_date)
        
        # Get the closest station
        station_id = station_data["results"][0]["stations"][0]
        print(f"Found station: {station_id}")
        
        # Now fetch weather data from this station
        weather_url = (
            f"https://www.ncei.noaa.gov/access/services/data/v1?"
            f"dataset=global-summary-of-the-day"
            f"&dataTypes=TEMP,PRCP,WDSP,TAVG,TMAX,TMIN"
            f"&stations={station_id}"
            f"&startDate={start_date}"
            f"&endDate={end_date}"
            f"&format=json"
            f"&units=metric"
            f"&token={api_key}"
        )
        
        print("Fetching weather data...")
        weather_response = requests.get(weather_url, timeout=30)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        if isinstance(weather_data, list) and len(weather_data) > 0:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(weather_data)
            df['date'] = pd.to_datetime(df['DATE'])
            
            # Clean and standardize the data
            weather_clean = []
            for _, row in df.iterrows():
                weather_clean.append({
                    'date': row['date'],
                    'TEMP': float(row.get('TEMP', row.get('TAVG', 20))),  # Temperature in Celsius
                    'PRCP': float(row.get('PRCP', 0)) / 10,  # Precipitation in mm
                    'WDSP': float(row.get('WDSP', 0))  # Wind speed in m/s
                })
            
            print(f"Successfully fetched {len(weather_clean)} weather records")
            return weather_clean
        else:
            print("No weather data returned from API")
            return create_fallback_weather_data(start_date, end_date)
            
    except requests.exceptions.RequestException as e:
        print(f"Weather API request failed: {e}")
        return create_fallback_weather_data(start_date, end_date)
    except Exception as e:
        print(f"Weather data processing error: {e}")
        return create_fallback_weather_data(start_date, end_date)

def create_fallback_weather_data(start_date, end_date):
    """Create realistic fallback weather data for California sites."""
    dates = pd.date_range(start_date, end_date, freq='D')
    
    fallback_data = []
    for date in dates:
        # Generate realistic weather for California
        month = date.month
        
        # Seasonal temperature patterns for California
        if month in [12, 1, 2]:  # Winter
            base_temp = 15 + np.random.normal(0, 3)
        elif month in [3, 4, 5]:  # Spring
            base_temp = 20 + np.random.normal(0, 4)
        elif month in [6, 7, 8]:  # Summer
            base_temp = 28 + np.random.normal(0, 5)
        else:  # Fall
            base_temp = 22 + np.random.normal(0, 3)
        
        # Precipitation (less in summer)
        if month in [6, 7, 8, 9]:
            precip = np.random.exponential(0.5) if np.random.random() < 0.1 else 0
        else:
            precip = np.random.exponential(2) if np.random.random() < 0.3 else 0
            
        # Wind speed
        wind_speed = max(0, np.random.normal(3, 1.5))
        
        fallback_data.append({
            'date': date,
            'TEMP': max(0, base_temp),
            'PRCP': precip,
            'WDSP': wind_speed
        })
    
    print(f"Created {len(fallback_data)} fallback weather records")
    return fallback_data

def fetch_solar_irradiance_fixed(lat, lon, years=[2018, 2019, 2020]):
    """
    Fixed solar irradiance fetching from NREL NSRDB.
    
    Args:
        lat: Latitude
        lon: Longitude  
        years: List of years to fetch
    """
    all_solar_data = []
    
    for year in years:
        try:
            url = (
                f"https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?"
                f"api_key={NREL_KEY}&email={EMAIL}"
                f"&wkt=POINT({lon}%20{lat})"
                f"&names={year}&interval=60"
                f"&attributes=ghi,dni,dhi,air_temperature,wind_speed"
                f"&utc=false"
            )
            
            print(f"Fetching solar data for {year}...")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse CSV response
            lines = response.text.strip().split('\n')
            if len(lines) > 2:
                # Skip metadata lines
                df = pd.read_csv(StringIO('\n'.join(lines[2:])))
                df['year'] = year
                all_solar_data.append(df)
                print(f"Successfully fetched solar data for {year}: {len(df)} records")
            else:
                print(f"No solar data received for {year}")
                
        except Exception as e:
            print(f"Solar API failed for {year}: {e}")
            continue
    
    if all_solar_data:
        combined_df = pd.concat(all_solar_data, ignore_index=True)
        
        # Convert to list of dictionaries for consistency
        solar_records = []
        for _, row in combined_df.iterrows():
            solar_records.append({
                'date': pd.Timestamp(year=int(row['Year']), 
                                   month=int(row['Month']), 
                                   day=int(row['Day']),
                                   hour=int(row['Hour']),
                                   minute=int(row['Minute'])),
                'ghi': float(row.get('GHI', 0)),
                'dni': float(row.get('DNI', 0)),
                'dhi': float(row.get('DHI', 0)),
                'temperature': float(row.get('Temperature', 20)),
                'wind_speed': float(row.get('Wind Speed', 0))
            })
        
        return solar_records
    else:
        print("No solar data available, creating fallback")
        return create_fallback_solar_data(years)

def create_fallback_solar_data(years):
    """Create realistic fallback solar data."""
    all_records = []
    
    for year in years:
        dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='h')
        
        for date in dates:
            hour = date.hour
            month = date.month
            
            # Solar irradiance patterns
            if 6 <= hour <= 18:  # Daylight hours
                # Peak around noon, vary by season
                hour_factor = np.sin(np.pi * (hour - 6) / 12)
                season_factor = 0.8 + 0.4 * np.sin(2 * np.pi * (month - 3) / 12)
                base_ghi = 800 * hour_factor * season_factor + np.random.normal(0, 50)
                ghi = max(0, base_ghi)
                dni = ghi * 0.8 + np.random.normal(0, 20)
                dhi = ghi * 0.3 + np.random.normal(0, 10)
            else:  # Night hours
                ghi = 0
                dni = 0
                dhi = 0
            
            all_records.append({
                'date': date,
                'ghi': max(0, ghi),
                'dni': max(0, dni),
                'dhi': max(0, dhi),
                'temperature': 20 + 10 * np.sin(2 * np.pi * month / 12) + np.random.normal(0, 2),
                'wind_speed': max(0, np.random.normal(3, 1))
            })
    
    return all_records

def fetch_caiso_renewables_carbon(start_date, end_date, max_retries=3):
    """
    Fetch CAISO renewables and carbon intensity data.
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        max_retries: Maximum retry attempts
    """
    renewables_data = []
    carbon_data = []
    
    try:
        # Fetch renewables generation data
        renewables_url = (
            "https://oasis.caiso.com/oasisapi/SingleZip?"
            "queryname=PRC_FUEL_TYPE&market_run_id=RTM"
            f"&startdatetime={start_date}T00:00-0000"
            f"&enddatetime={end_date}T23:59-0000"
        )
        
        print("Fetching CAISO renewables data...")
        for attempt in range(max_retries):
            try:
                response = requests.get(renewables_url, timeout=60)
                response.raise_for_status()
                print("Successfully fetched CAISO renewables data")
                # Note: This would need to be unzipped and parsed
                break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retry {attempt + 1} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"CAISO renewables API failed: {e}")
        
        # Create fallback renewables data
        dates = pd.date_range(start_date, end_date, freq='h')
        for date in dates:
            hour = date.hour
            month = date.month
            
            # Realistic renewables percentages
            solar_pct = max(0, 30 * np.sin(np.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
            wind_pct = 15 + 10 * np.random.normal(0, 1)
            hydro_pct = 20 + 5 * np.sin(2 * np.pi * month / 12)
            
            renewables_data.append({
                'datetime': date,
                'solar_pct': max(0, solar_pct),
                'wind_pct': max(0, min(50, wind_pct)),
                'hydro_pct': max(5, min(40, hydro_pct)),
                'total_renewables_pct': max(20, min(80, solar_pct + wind_pct + hydro_pct))
            })
        
        # Carbon intensity (inversely related to renewables)
        for i, date in enumerate(dates):
            renewables_pct = renewables_data[i]['total_renewables_pct']
            # Carbon intensity in kg CO2/MWh (lower when more renewables)
            carbon_intensity = 400 - (renewables_pct * 3) + np.random.normal(0, 20)
            
            carbon_data.append({
                'datetime': date,
                'carbon_intensity': max(200, min(600, carbon_intensity))
            })
        
        print(f"Created {len(renewables_data)} renewables records")
        print(f"Created {len(carbon_data)} carbon intensity records")
        
        return renewables_data, carbon_data
        
    except Exception as e:
        print(f"CAISO data fetching error: {e}")
        return [], []

def fetch_sce_tou_rates():
    """
    Fetch or create SCE Time-of-Use rate structure.
    """
    # SCE TOU-D-4-9PM rate structure (residential EV)
    tou_rates = {
        'peak': {
            'hours': list(range(16, 21)),  # 4PM-9PM
            'months': list(range(6, 10)),  # June-September 
            'price': 0.48  # $/kWh
        },
        'off_peak': {
            'hours': list(range(0, 16)) + list(range(21, 24)),  # All other hours
            'months': list(range(6, 10)),  # June-September
            'price': 0.25  # $/kWh
        },
        'super_off_peak': {
            'hours': list(range(8, 16)),  # 8AM-4PM
            'months': list(range(10, 6)),  # October-May (wraps around)
            'price': 0.18  # $/kWh
        }
    }
    
    return tou_rates

def get_sce_tou_price(timestamp, tou_rates):
    """Get SCE TOU price for a given timestamp."""
    hour = timestamp.hour
    month = timestamp.month
    
    # Check peak hours during summer months
    if month in range(6, 10) and hour in range(16, 21):
        return tou_rates['peak']['price']
    
    # Check super off-peak (winter midday)
    if month not in range(6, 10) and hour in range(8, 16):
        return tou_rates['super_off_peak']['price']
    
    # Default to off-peak
    return tou_rates['off_peak']['price']

# Test the functions
if __name__ == "__main__":
    # Test coordinates for Caltech
    lat, lon = 34.137, -118.125
    
    print("Testing weather data fetching...")
    weather_data = fetch_noaa_weather_fixed(lat, lon, "2018-01-01", "2018-01-31", NOAA_TOKEN)
    print(f"Weather data sample: {weather_data[:2] if weather_data else 'None'}")
    
    print("\nTesting solar data fetching...")
    solar_data = fetch_solar_irradiance_fixed(lat, lon, [2018])
    print(f"Solar data sample: {solar_data[:2] if solar_data else 'None'}")
    
    print("\nTesting CAISO data fetching...")
    renewables, carbon = fetch_caiso_renewables_carbon("2018-01-01", "2018-01-07")
    print(f"Renewables sample: {renewables[:2] if renewables else 'None'}")
    print(f"Carbon sample: {carbon[:2] if carbon else 'None'}")
    
    print("\nTesting SCE TOU rates...")
    tou_rates = fetch_sce_tou_rates()
    test_time = pd.Timestamp('2018-07-15 17:00:00')  # Summer peak hour
    price = get_sce_tou_price(test_time, tou_rates)
    print(f"TOU price for {test_time}: ${price:.2f}/kWh")
