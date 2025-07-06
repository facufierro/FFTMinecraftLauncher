#!/usr/bin/env python
"""Debug script to check launcher profiles and instance resolution."""

import json
from pathlib import Path
import os

# Read the launcher profiles
minecraft_dir = Path(os.environ['APPDATA']) / '.minecraft'
launcher_profiles = minecraft_dir / 'launcher_profiles.json'

print('=== LAUNCHER PROFILES DEBUG ===')
if launcher_profiles.exists():
    with open(launcher_profiles, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    print('All profiles found:')
    for profile_id, profile_data in profiles.get('profiles', {}).items():
        profile_name = profile_data.get('name', profile_id)
        game_dir = profile_data.get('gameDir', 'Not specified (uses default)')
        print(f'Profile ID: {profile_id}')
        print(f'  Name: "{profile_name}"')
        print(f'  GameDir: {game_dir}')
        print()
    
    # Now test the specific instance lookup
    print('=== TESTING INSTANCE RESOLUTION ===')
    for target_instance in ['NeoForge', 'FFClient']:
        print(f'Looking for instance: "{target_instance}"')
        found = False
        for profile_id, profile_data in profiles.get('profiles', {}).items():
            profile_name = profile_data.get('name', profile_id)
            if profile_name == target_instance:
                game_dir = profile_data.get('gameDir', str(minecraft_dir))
                print(f'  FOUND! GameDir: {game_dir}')
                # Check if path exists
                if isinstance(game_dir, str) and game_dir != str(minecraft_dir):
                    path_obj = Path(game_dir)
                    print(f'  Path exists: {path_obj.exists()}')
                found = True
                break
        if not found:
            print(f'  NOT FOUND in profiles!')
        print()
else:
    print('launcher_profiles.json not found!')

# Test the actual config resolution
print('=== CONFIG RESOLUTION TEST ===')
from src.models.config import LauncherConfig

config = LauncherConfig.load_from_file('launcher_config.json')
print(f'Config selected_instance: "{config.selected_instance}"')

# Test instance path resolution
instance_path = config.get_selected_instance_path()
print(f'Resolved instance path: {instance_path}')

# Test NeoForge service resolution
from src.services.neoforge_service import NeoForgeService
neoforge_service = NeoForgeService(config)
neoforge_path = neoforge_service._find_instance_path(config.selected_instance)
print(f'NeoForge service resolution: {neoforge_path}')
