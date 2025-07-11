#!/usr/bin/env python3
"""
FFT Launcher Profile Cleanup Utility

This script fixes corrupted launcher profiles that have extremely long icon strings,
which can cause the Minecraft launcher to fail or create broken profile files.

Usage:
    python fix_launcher_profiles.py

This script will:
1. Scan the main .minecraft directory for launcher_profiles.json
2. Find any profiles with corrupted icon data (very long strings)
3. Replace corrupted icons with safe default icons ("Furnace")
4. Backup the original file before making changes
5. Save the cleaned profile file

The script is safe to run and will create a backup before making any changes.
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


def backup_file(file_path: Path) -> Path:
    """Create a backup of the file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_name(f"{file_path.stem}_backup_{timestamp}{file_path.suffix}")
    shutil.copy2(file_path, backup_path)
    return backup_path


def clean_launcher_profiles(profiles_path: Path) -> dict:
    """Clean corrupted launcher profiles and return cleanup statistics."""
    stats = {
        "profiles_scanned": 0,
        "profiles_fixed": 0,
        "corrupted_icons_fixed": 0,
        "empty_icons_fixed": 0,
        "missing_icons_added": 0
    }
    
    if not profiles_path.exists():
        print(f"❌ Launcher profiles file not found: {profiles_path}")
        return stats
    
    print(f"📄 Loading launcher profiles from: {profiles_path}")
    
    # Load the profiles
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load profiles file: {e}")
        return stats
    
    # Create backup before making changes
    try:
        backup_path = backup_file(profiles_path)
        print(f"💾 Created backup: {backup_path.name}")
    except Exception as e:
        print(f"⚠️  Warning: Failed to create backup: {e}")
    
    # Process each profile
    profiles_cleaned = False
    for profile_id, profile_data in profiles_data.get("profiles", {}).items():
        stats["profiles_scanned"] += 1
        profile_name = profile_data.get("name", profile_id)
        profile_fixed = False
        
        if "icon" in profile_data:
            icon_value = profile_data["icon"]
            
            # Check for extremely long icon strings (likely base64 encoded images)
            if isinstance(icon_value, str) and len(icon_value) > 100:
                print(f"🔧 Fixing corrupted long icon string in profile: '{profile_name}' (length: {len(icon_value)})")
                profile_data["icon"] = "Furnace"
                stats["corrupted_icons_fixed"] += 1
                profile_fixed = True
                
            # Fix empty or null icons
            elif icon_value is None or icon_value == "":
                print(f"🔧 Fixing empty icon in profile: '{profile_name}'")
                profile_data["icon"] = "Furnace"
                stats["empty_icons_fixed"] += 1
                profile_fixed = True
                
        elif profile_data.get("type") == "custom":
            # Add missing icon to custom profiles
            print(f"🔧 Adding missing icon to custom profile: '{profile_name}'")
            profile_data["icon"] = "Furnace"
            stats["missing_icons_added"] += 1
            profile_fixed = True
        
        if profile_fixed:
            stats["profiles_fixed"] += 1
            profiles_cleaned = True
    
    # Save the cleaned profiles if changes were made
    if profiles_cleaned:
        try:
            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2)
            print(f"✅ Successfully saved cleaned profiles to: {profiles_path}")
        except Exception as e:
            print(f"❌ Failed to save cleaned profiles: {e}")
            return stats
    else:
        print("✅ No corrupted profiles found - file is already clean!")
    
    return stats


def main():
    """Main entry point for the profile cleanup utility."""
    print("🚀 FFT Launcher Profile Cleanup Utility")
    print("=" * 50)
    print()
    
    # Find the main .minecraft directory
    minecraft_dir = Path(os.environ.get('APPDATA', '')) / ".minecraft"
    
    if not minecraft_dir.exists():
        print(f"❌ Minecraft directory not found: {minecraft_dir}")
        print("Make sure Minecraft is installed and has been run at least once.")
        return 1
    
    profiles_path = minecraft_dir / "launcher_profiles.json"
    
    print(f"🔍 Scanning Minecraft directory: {minecraft_dir}")
    
    # Clean the main launcher profiles
    stats = clean_launcher_profiles(profiles_path)
    
    # Print summary
    print()
    print("📊 Cleanup Summary:")
    print(f"   Profiles scanned: {stats['profiles_scanned']}")
    print(f"   Profiles fixed: {stats['profiles_fixed']}")
    print(f"   Corrupted icons fixed: {stats['corrupted_icons_fixed']}")
    print(f"   Empty icons fixed: {stats['empty_icons_fixed']}")
    print(f"   Missing icons added: {stats['missing_icons_added']}")
    
    if stats['profiles_fixed'] > 0:
        print()
        print("✅ Profile cleanup completed successfully!")
        print("Your Minecraft launcher should now work properly.")
    else:
        print()
        print("ℹ️  No issues found - your profiles are already clean!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
