#!/usr/bin/env python3
"""
Setup script to help configure API tokens for data sources.
"""

import os
import sys

def setup_noaa_token():
    """Interactive setup for NOAA API token."""
    print("\n=== NOAA API Token Setup ===")
    print("To get a NOAA API token:")
    print("1. Go to: https://www.ncdc.noaa.gov/cdo-web/token")
    print("2. Sign up for a free account if you don't have one")
    print("3. Generate a new token")
    print("4. Copy the token")
    
    token = input("\nEnter your NOAA API token (or press Enter to skip): ").strip()
    
    if token:
        # Set environment variable for current session
        os.environ["NOAA_API_TOKEN"] = token
        print(f"✅ NOAA API token set for current session")
        
        # Ask if they want to make it permanent
        permanent = input("Make this permanent by adding to your shell profile? (y/n): ").strip().lower()
        
        if permanent == 'y':
            shell_profile = None
            home_dir = os.path.expanduser("~")
            
            # Detect shell and profile file
            if os.path.exists(os.path.join(home_dir, ".zshrc")):
                shell_profile = os.path.join(home_dir, ".zshrc")
            elif os.path.exists(os.path.join(home_dir, ".bashrc")):
                shell_profile = os.path.join(home_dir, ".bashrc")
            elif os.path.exists(os.path.join(home_dir, ".profile")):
                shell_profile = os.path.join(home_dir, ".profile")
            
            if shell_profile:
                export_line = f'\nexport NOAA_API_TOKEN="{token}"\n'
                try:
                    with open(shell_profile, "a") as f:
                        f.write(export_line)
                    print(f"✅ Added to {shell_profile}")
                    print("Please restart your terminal or run: source " + shell_profile)
                except Exception as e:
                    print(f"❌ Error writing to {shell_profile}: {e}")
                    print("You can manually add this line to your shell profile:")
                    print(f'export NOAA_API_TOKEN="{token}"')
            else:
                print("❌ Could not find shell profile file")
                print("You can manually add this line to your shell profile:")
                print(f'export NOAA_API_TOKEN="{token}"')
    else:
        print("⏭️  Skipped NOAA token setup")

def main():
    """Main setup function."""
    print("🔧 API Token Setup for Data Sources")
    print("=" * 40)
    
    # Check current environment
    current_token = os.getenv("NOAA_API_TOKEN")
    if current_token and current_token != "YOUR_DEFAULT_TOKEN":
        print(f"✅ NOAA API token is already set: {current_token[:10]}...")
        update = input("Update NOAA token? (y/n): ").strip().lower()
        if update == 'y':
            setup_noaa_token()
    else:
        setup_noaa_token()
    
    print("\n🎉 Setup complete!")
    print("\nTo test your configuration, run:")
    print("python services/backend/datasources/fetch_data.py --source noaa --days 1")

if __name__ == "__main__":
    main()

