import logging
import json
import os
from ..models.profile import Profile


class ProfileService:
    def __init__(self, minecraft_dir: str):

        logging.debug("Initializing ProfileService")
        self.profile = Profile(
            id="a4e7d1b6b0974c87bd556f8db97afda3",
            created="2023-10-01T12:00:00Z",
            icon="Furnace",
            lastUsed="2025-07-11T16:45:20.8297Z",
            lastVersionId="neoforge-21.1.192",
            name="FFTClient",
            type="custom",
        )
        self.profile_file = os.path.join(minecraft_dir, "launcher_profiles.json")

    def _is_update_required(self):
        if os.path.exists(self.profile_file):
            with open(self.profile_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}
        profiles = data.get("profiles", {})
        for profile_info in profiles.values():
            if profile_info.get("name") == self.profile.name:
                return False  # Profile exists, no update needed
        return True  # Profile missing, update needed

    def update(self):
        logging.info("Ensuring FFTClient profile exists in launcher_profiles.json")
        try:
            if not self._is_update_required():
                logging.info(
                    f"Profile '{self.profile.name}' already exists, skipping add."
                )
                return
            # Read the existing launcher_profiles.json
            if os.path.exists(self.profile_file):
                with open(self.profile_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
            else:
                data = {}
            profiles = data.get("profiles", {})
            # Add the profile
            profiles[self.profile.id] = self.profile.__dict__
            data["profiles"] = profiles
            # Write back the updated data
            with open(self.profile_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            logging.info("Profile data updated successfully")
        except Exception as e:
            logging.error("Failed to update profile data: %s", e)
            raise
