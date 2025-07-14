import logging
import json
from ..models.profile import Profile
from ..models.constants import Paths, PROFILE_DATA


class ProfileService:
    def __init__(self):
        logging.debug("Initializing ProfileService")
        self.default_profile = Paths.DEFAULT_PROFILE_FILE.value

    def get_profile_data(self):
        try:
            logging.debug(
                "Attempting to read profile data from: %s", self.default_profile
            )
            with open(self.default_profile, "r", encoding="utf-8") as file:
                data = json.load(file)
            profiles = data.get("profiles", {})
            for profile_id, profile_info in profiles.items():
                if profile_info.get("name") == "FFTClient":
                    profile_info["id"] = profile_id
                    return Profile(**profile_info)
            logging.warning("FFTClient profile not found in: %s", self.default_profile)
            return None
        except FileNotFoundError:
            logging.error("Profile data file not found: %s", self.default_profile)
            return None

    def update_profile(self):
        logging.info("Updating profile data by appending new profile entry")
        try:
            # Read the existing launcher_profiles.json
            with open(self.default_profile, "r", encoding="utf-8") as file:
                data = json.load(file)
            profiles = data.get("profiles", {})

            # Add new profile(s) from PROFILE_DATA
            for profile_id, profile_info in PROFILE_DATA.items():
                if profile_id not in profiles:
                    profiles[profile_id] = profile_info
                    logging.info(f"Added new profile: {profile_id}")
                else:
                    logging.info(f"Profile {profile_id} already exists, skipping.")

            data["profiles"] = profiles

            # Write back the updated data
            with open(self.default_profile, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            logging.info("Profile data updated successfully")
        except Exception as e:
            logging.error("Failed to update profile data: %s", e)
            raise

    def delete_profile(self):
        # Logic to delete the profile
        self.profile = None
