#!/usr/bin/env python3
"""
Simple script to update files on the Pi
"""
import subprocess
import sys

def copy_file_to_pi(local_file, remote_path):
    """Copy a file to the Pi using scp"""
    try:
        cmd = ['scp', local_file, f'ledpi@ledpi:{remote_path}']
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully copied {local_file} to {remote_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error copying {local_file}: {e}")
        print(f"stderr: {e.stderr}")
        return False

if __name__ == "__main__":
    # Copy the updated web interface file
    success1 = copy_file_to_pi('web_interface_v2.py', '/home/ledpi/LEDMatrix/')
    
    # Copy the updated template file
    success2 = copy_file_to_pi('templates/index_v2.html', '/home/ledpi/LEDMatrix/templates/')
    
    if success1 and success2:
        print("All files copied successfully!")
        print("You can now restart the web interface on the Pi.")
    else:
        print("Some files failed to copy. Please check the errors above.")
        sys.exit(1)
