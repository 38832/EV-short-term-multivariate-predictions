# Test the updated functions
import pandas as pd
import numpy as np
from datetime import datetime

# Test coordinates for Caltech
lat, lon = 34.137, -118.125
NOAA_TOKEN = "BzYUIRtaVJtrXGcvpfHfppNbiRQrbpqT"

print("=== Testing Updated EV Proposal Functions ===")

# Test the working weather function 
try:
    from updated_ev_prposal import fetch_weather_data_working
    print("\n✓ Successfully imported fetch_weather_data_working")
except ImportError as e:
    print(f"\n✗ Import error: {e}")

# Test CAISO function
try:
    from updated_ev_prposal import fetch_caiso_renewables_carbon_working
    print("✓ Successfully imported fetch_caiso_renewables_carbon_working")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Test enhanced TOU pricing
try:
    from updated_ev_prposal import get_sce_tou_price_working
    test_time = pd.Timestamp('2018-07-15 17:00:00')
    price = get_sce_tou_price_working(test_time)
    print(f"✓ TOU pricing works: ${price:.2f}/kWh for summer Sunday 5PM")
except Exception as e:
    print(f"✗ TOU pricing error: {e}")

# Test solar function
try:
    from updated_ev_prposal import fetch_solar_irradiance_working
    print("✓ Successfully imported fetch_solar_irradiance_working")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Test enhanced feature engineering
try:
    from updated_ev_prposal import add_exogenous_features_enhanced
    print("✓ Successfully imported add_exogenous_features_enhanced")
except ImportError as e:
    print(f"✗ Import error: {e}")

print("\n=== Import Test Summary ===")
print("All critical functions should be successfully imported.")
print("If any import failed, there may be syntax errors to fix.")

# Quick functionality test
try:
    print("\n=== Quick Functionality Test ===")
    
    # Test CAISO data generation
    renewables_data, carbon_data = fetch_caiso_renewables_carbon_working('2018-01-01', '2018-01-02')
    if renewables_data and carbon_data:
        print(f"✓ CAISO data: {len(renewables_data)} renewables, {len(carbon_data)} carbon records")
        avg_renewables = np.mean([r['total_renewables_pct'] for r in renewables_data])
        print(f"  Average renewables: {avg_renewables:.1f}%")
    else:
        print("✗ CAISO data generation failed")
        
except Exception as e:
    print(f"✗ Functionality test error: {e}")

print("\n=== Test Complete ===")
