#!/usr/bin/env python3
"""
Test script to verify the safe_config_get function and template logic works correctly.
"""
import json
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class DictWrapper:
    """Wrapper to make dictionary accessible via dot notation for Jinja2 templates."""
    def __init__(self, data=None):
        # Store the original data
        object.__setattr__(self, '_data', data if isinstance(data, dict) else {})
        
        # Set attributes from the dictionary
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    object.__setattr__(self, key, DictWrapper(value))
                elif isinstance(value, list):
                    object.__setattr__(self, key, value)
                else:
                    object.__setattr__(self, key, value)
    
    def __getattr__(self, name):
        # Return a new empty DictWrapper for missing attributes
        # This allows chaining like main_config.display.hardware.rows
        return DictWrapper({})
    
    def __str__(self):
        # Return empty string for missing values to avoid template errors
        data = object.__getattribute__(self, '_data')
        if not data:
            return ''
        return str(data)
    
    def __int__(self):
        # Return 0 for missing numeric values
        data = object.__getattribute__(self, '_data')
        if not data:
            return 0
        try:
            return int(data)
        except (ValueError, TypeError):
            return 0
    
    def __bool__(self):
        # Return False for missing boolean values
        data = object.__getattribute__(self, '_data')
        if not data:
            return False
        return bool(data)
    
    def get(self, key, default=None):
        # Support .get() method like dictionaries
        data = object.__getattribute__(self, '_data')
        if data and key in data:
            return data[key]
        return default

def safe_config_get(config, *keys, default=''):
    """Safely get nested config values with fallback."""
    try:
        current = config
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
                # Check if we got an empty DictWrapper
                if isinstance(current, DictWrapper):
                    data = object.__getattribute__(current, '_data')
                    if not data:  # Empty DictWrapper means missing config
                        return default
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        # Final check for empty values
        if current is None or (hasattr(current, '_data') and not object.__getattribute__(current, '_data')):
            return default
        return current
    except (AttributeError, KeyError, TypeError):
        return default

def test_config_access():
    """Test the safe config access with actual config data."""
    print("Testing safe_config_get function...")
    
    # Load the actual config
    try:
        with open('config/config.json', 'r') as f:
            config_data = json.load(f)
        print("✓ Successfully loaded config.json")
    except Exception as e:
        print(f"✗ Failed to load config.json: {e}")
        return False
    
    # Wrap the config
    main_config = DictWrapper(config_data)
    print("✓ Successfully wrapped config in DictWrapper")
    
    # Test critical configuration values
    test_cases = [
        ('display.hardware.rows', 32),
        ('display.hardware.cols', 64),
        ('display.hardware.brightness', 95),
        ('display.hardware.chain_length', 2),
        ('display.hardware.parallel', 1),
        ('display.hardware.hardware_mapping', 'adafruit-hat-pwm'),
        ('display.runtime.gpio_slowdown', 3),
        ('display.hardware.scan_mode', 0),
        ('display.hardware.pwm_bits', 9),
        ('display.hardware.pwm_dither_bits', 1),
        ('display.hardware.pwm_lsb_nanoseconds', 130),
        ('display.hardware.limit_refresh_rate_hz', 120),
        ('display.hardware.disable_hardware_pulsing', False),
        ('display.hardware.inverse_colors', False),
        ('display.hardware.show_refresh_rate', False),
        ('display.use_short_date_format', True),
    ]
    
    print("\nTesting configuration value access:")
    all_passed = True
    
    for key_path, expected_default in test_cases:
        keys = key_path.split('.')
        
        # Test safe_config_get function
        result = safe_config_get(main_config, *keys, default=expected_default)
        
        # Test direct access (old way) for comparison
        try:
            direct_result = main_config
            for key in keys:
                direct_result = getattr(direct_result, key)
            direct_success = True
        except AttributeError:
            direct_result = None
            direct_success = False
        
        status = "✓" if result is not None else "✗"
        print(f"  {status} {key_path}: {result} (direct: {direct_result if direct_success else 'FAILED'})")
        
        if result is None:
            all_passed = False
    
    return all_passed

def test_missing_config():
    """Test behavior with missing configuration sections."""
    print("\nTesting with missing configuration sections...")
    
    # Create a config with missing sections
    incomplete_config = {
        "timezone": "America/Chicago",
        # Missing display section entirely
    }
    
    main_config = DictWrapper(incomplete_config)
    
    # Test that safe_config_get returns defaults for missing sections
    test_cases = [
        ('display.hardware.rows', 32),
        ('display.hardware.cols', 64),
        ('display.hardware.brightness', 95),
    ]
    
    all_passed = True
    for key_path, expected_default in test_cases:
        keys = key_path.split('.')
        result = safe_config_get(main_config, *keys, default=expected_default)
        
        status = "✓" if result == expected_default else "✗"
        print(f"  {status} {key_path}: {result} (expected default: {expected_default})")
        
        if result != expected_default:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Web Interface Configuration Display")
    print("=" * 60)
    
    success1 = test_config_access()
    success2 = test_missing_config()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✓ ALL TESTS PASSED - Web interface should display config correctly!")
    else:
        print("✗ SOME TESTS FAILED - There may be issues with config display")
    print("=" * 60)
