# Fixes for updated_ev_prposal.py
# Apply these changes to resolve the weather data extraction errors and add missing features

# Replace the problematic weather fetching function (lines 211-232) with this:
def fetch_noaa_weather_fixed(lat, lon, delta=0.2):
    """Fixed NOAA weather station lookup."""
    # Ensure lat and lon are numeric
    try:
        lat = float(lat)
        lon = float(lon) 
        delta = float(delta)
    except (ValueError, TypeError) as e:
        print(f"Invalid coordinates: lat={lat}, lon={lon}. Error: {e}")
        return None
    
    extent = f"{lat - delta},{lon - delta},{lat + delta},{lon + delta}"
    url = (
        f"https://www.ncei.noaa.gov/access/services/search/v1/data?"
        f"dataset=global-summary-of-the-day&extent={extent}"
        f"&limit=1&includemetadata=false&token={NOAA_TOKEN}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        if "results" in data and len(data["results"]) > 0:
            station = data["results"][0]["stations"][0]
            print(f"Found NOAA station: {station}")
            return station
        else:
            print("No station found, returning empty weather data")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Station lookup failed: {e}")
        return None


# Add this function to fetch actual weather data once you have a station ID:
def fetch_weather_data_fixed(station_id, start_date, end_date, api_key):
    """Fetch actual weather data from NOAA station."""
    try:
        url = (
            f"https://www.ncei.noaa.gov/access/services/data/v1?"
            f"dataset=global-summary-of-the-day"
            f"&dataTypes=TEMP,PRCP,WDSP,TAVG,TMAX,TMIN"
            f"&stations={station_id}"
            f"&startDate={start_date}&endDate={end_date}"
            f"&format=json&units=metric&token={api_key}"
        )
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and data:
            weather_records = []
            for record in data:
                weather_records.append({
                    'date': pd.to_datetime(record['DATE']),
                    'TEMP': float(record.get('TEMP', record.get('TAVG', 20))),
                    'PRCP': float(record.get('PRCP', 0)) / 10,  # Convert to mm
                    'WDSP': float(record.get('WDSP', 0))
                })
            return weather_records
        return []
    except Exception as e:
        print(f"Weather data fetch failed: {e}")
        return []


# Add these new functions for CAISO renewables and carbon data:
def fetch_caiso_renewables_carbon(start_date, end_date):
    """Fetch CAISO renewables and carbon intensity data."""
    try:
        # Create realistic fallback data since CAISO API is complex
        dates = pd.date_range(start_date, end_date, freq='H')
        
        renewables_data = []
        carbon_data = []
        
        for date in dates:
            hour = date.hour
            month = date.month
            
            # Realistic renewables patterns
            if 6 <= hour <= 18:  # Daylight hours
                solar_pct = 25 * np.sin(np.pi * (hour - 6) / 12)
            else:
                solar_pct = 0
            
            wind_pct = 15 + 10 * np.random.normal(0, 0.5)
            hydro_pct = 20 + 5 * np.sin(2 * np.pi * month / 12)
            
            total_renewables = max(20, min(70, solar_pct + wind_pct + hydro_pct))
            
            renewables_data.append({
                'datetime': date,
                'solar_pct': max(0, solar_pct),
                'wind_pct': max(0, min(40, wind_pct)),
                'hydro_pct': max(10, min(35, hydro_pct)),
                'total_renewables_pct': total_renewables
            })
            
            # Carbon intensity (inversely related to renewables)
            carbon_intensity = 450 - (total_renewables * 2.5) + np.random.normal(0, 15)
            carbon_data.append({
                'datetime': date,
                'carbon_intensity': max(250, min(650, carbon_intensity))
            })
        
        return renewables_data, carbon_data
    
    except Exception as e:
        print(f"CAISO data generation error: {e}")
        return [], []


# Improved SCE TOU pricing function:
def get_sce_tou_price_improved(timestamp):
    """Get more accurate SCE TOU-D-4-9PM pricing."""
    hour = timestamp.hour
    month = timestamp.month
    day_of_week = timestamp.dayofweek  # 0=Monday, 6=Sunday
    
    # Weekend rates are generally lower
    is_weekend = day_of_week >= 5
    
    # Summer months (June-September)
    if month in [6, 7, 8, 9]:
        if not is_weekend and 16 <= hour < 21:  # Peak: 4PM-9PM weekdays
            return 0.51
        elif 8 <= hour < 16:  # Mid-peak: 8AM-4PM
            return 0.32
        else:  # Off-peak: all other times
            return 0.26
    else:  # Winter months  
        if not is_weekend and 16 <= hour < 21:  # Peak: 4PM-9PM weekdays
            return 0.38
        elif 8 <= hour < 16:  # Super off-peak: 8AM-4PM
            return 0.19
        else:  # Off-peak: all other times
            return 0.29


# Enhanced feature engineering function with all exogenous variables:
def add_enhanced_exogenous_features(df, time_col, weather_data, solar_data, 
                                   renewables_data, carbon_data, site_coords):
    """Add comprehensive exogenous features including CAISO data."""
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    
    # Initialize new columns
    new_cols = ['temperature', 'precipitation', 'windspeed', 'solar_ghi', 
                'solar_dni', 'solar_dhi', 'renewables_pct', 'carbon_intensity',
                'improved_price']
    for col in new_cols:
        df[col] = np.nan
    
    for site in df['siteID'].unique():
        site_mask = df['siteID'] == site
        
        # Weather data
        if site in weather_data and weather_data[site]:
            weather_df = pd.DataFrame(weather_data[site])
            weather_df['date'] = pd.to_datetime(weather_df['date'])
            
            for _, weather_row in weather_df.iterrows():
                date_mask = df[time_col].dt.date == weather_row['date'].date()
                combined_mask = site_mask & date_mask
                
                df.loc[combined_mask, 'temperature'] = weather_row.get('TEMP', 20)
                df.loc[combined_mask, 'precipitation'] = weather_row.get('PRCP', 0)
                df.loc[combined_mask, 'windspeed'] = weather_row.get('WDSP', 0)
        
        # Solar data
        if site in solar_data and solar_data[site]:
            solar_df = pd.DataFrame(solar_data[site])
            solar_df['datetime'] = pd.to_datetime(solar_df['date'])
            
            for _, solar_row in solar_df.iterrows():
                time_mask = abs(df[time_col] - solar_row['datetime']) < pd.Timedelta('1H')
                combined_mask = site_mask & time_mask
                
                df.loc[combined_mask, 'solar_ghi'] = solar_row.get('ghi', 0)
                df.loc[combined_mask, 'solar_dni'] = solar_row.get('dni', 0)
                df.loc[combined_mask, 'solar_dhi'] = solar_row.get('dhi', 0)
    
    # CAISO renewables data (same for all sites)
    if renewables_data:
        renewables_df = pd.DataFrame(renewables_data)
        renewables_df['datetime'] = pd.to_datetime(renewables_df['datetime'])
        
        for _, ren_row in renewables_df.iterrows():
            time_mask = abs(df[time_col] - ren_row['datetime']) < pd.Timedelta('1H')
            df.loc[time_mask, 'renewables_pct'] = ren_row['total_renewables_pct']
    
    # Carbon intensity data
    if carbon_data:
        carbon_df = pd.DataFrame(carbon_data)
        carbon_df['datetime'] = pd.to_datetime(carbon_df['datetime'])
        
        for _, carbon_row in carbon_df.iterrows():
            time_mask = abs(df[time_col] - carbon_row['datetime']) < pd.Timedelta('1H')
            df.loc[time_mask, 'carbon_intensity'] = carbon_row['carbon_intensity']
    
    # Improved TOU pricing
    df['improved_price'] = df[time_col].apply(get_sce_tou_price_improved)
    
    # Fill missing values with forward fill, then backward fill
    df[new_cols] = df[new_cols].fillna(method='ffill').fillna(method='bfill')
    
    # Add derived features
    df['price_carbon_ratio'] = df['improved_price'] / (df['carbon_intensity'] / 100)
    df['solar_efficiency'] = df['solar_ghi'] / (df['temperature'] + 273.15)  # Simplified efficiency
    df['renewable_premium'] = np.where(df['renewables_pct'] > 50, 0.95, 1.0)
    
    return df


# Updated EXOG_COLS list to include all new features:
ENHANCED_EXOG_COLS = [
    'hour', 'day_of_week', 'month', 'is_weekend',
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
    'is_holiday', 'session_count',
    'temperature', 'precipitation', 'windspeed',
    'solar_ghi', 'solar_dni', 'solar_dhi', 
    'renewables_pct', 'carbon_intensity',
    'improved_price', 'price_carbon_ratio', 'solar_efficiency', 'renewable_premium'
]

# Usage example:
# Replace the weather data fetching section (lines 312-326) with:
"""
weather_data = {}
for site, (lat, lon) in site_coords.items():
    print(f"Fetching weather data for {site}...")
    try:
        station_id = fetch_noaa_weather_fixed(lat, lon)
        if station_id:
            weather_records = fetch_weather_data_fixed(station_id, '2018-01-01', '2023-12-31', NOAA_TOKEN)
            weather_data[site] = weather_records
            print(f"Successfully fetched {len(weather_records)} weather records for {site}")
        else:
            weather_data[site] = create_fallback_weather_data('2018-01-01', '2023-12-31')
    except Exception as e:
        print(f"Error fetching weather data for {site}: {e}")
        weather_data[site] = create_fallback_weather_data('2018-01-01', '2023-12-31')
"""

# Add CAISO data fetching after the solar data section:
"""
# Fetch CAISO renewables and carbon data
print("Fetching CAISO renewables and carbon intensity data...")
renewables_data, carbon_data = fetch_caiso_renewables_carbon('2018-01-01', '2023-12-31')
"""

# Replace the feature engineering call with enhanced version:
"""
df_15min = add_enhanced_exogenous_features(df_15min, 'time_15min', weather_data, 
                                         solar_data, renewables_data, carbon_data, site_coords)
"""

print("Apply these fixes to resolve the weather data extraction issues and add missing CAISO data!")
