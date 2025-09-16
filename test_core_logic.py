#!/usr/bin/env python3
"""
Test the core logic of the web interface without Flask dependencies.
"""
import json

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

def safe_get(obj, key_path, default=''):
    """Safely access nested dictionary values using dot notation."""
    try:
        keys = key_path.split('.')
        current = obj
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
            elif isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default
    except (AttributeError, KeyError, TypeError):
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

def simulate_template_rendering():
    """Simulate how the template would render configuration values."""
    print("Simulating template rendering with actual config...")
    
    # Load actual config
    with open('config/config.json', 'r') as f:
        config_data = json.load(f)
    
    main_config = DictWrapper(config_data)
    
    # Simulate template expressions that would be used
    template_tests = [
        # Input field values
        ("safe_config_get(main_config, 'display', 'hardware', 'rows', default=32)", 32),
        ("safe_config_get(main_config, 'display', 'hardware', 'cols', default=64)", 64),
        ("safe_config_get(main_config, 'display', 'hardware', 'brightness', default=95)", 95),
        ("safe_config_get(main_config, 'display', 'hardware', 'chain_length', default=2)", 2),
        ("safe_config_get(main_config, 'display', 'hardware', 'parallel', default=1)", 1),
        ("safe_config_get(main_config, 'display', 'hardware', 'hardware_mapping', default='adafruit-hat-pwm')", 'adafruit-hat-pwm'),
        
        # Checkbox states
        ("safe_config_get(main_config, 'display', 'hardware', 'disable_hardware_pulsing', default=False)", False),
        ("safe_config_get(main_config, 'display', 'hardware', 'inverse_colors', default=False)", False),
        ("safe_config_get(main_config, 'display', 'hardware', 'show_refresh_rate', default=False)", False),
        ("safe_config_get(main_config, 'display', 'use_short_date_format', default=True)", True),
    ]
    
    all_passed = True
    for expression, expected in template_tests:
        try:
            result = eval(expression)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {expression.split('(')[0]}(...): {result} (expected: {expected})")
            if result != expected:
                all_passed = False
        except Exception as e:
            print(f"  ✗ {expression}: ERROR - {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("=" * 70)
    print("Testing Core Web Interface Logic")
    print("=" * 70)
    
    success = simulate_template_rendering()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ ALL TEMPLATE SIMULATIONS PASSED!")
        print("✓ The web interface should correctly display all config values!")
    else:
        print("✗ SOME TEMPLATE SIMULATIONS FAILED!")
        print("✗ There may be issues with config display in the web interface!")
    print("=" * 70)
