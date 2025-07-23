import json
import logging
import requests
import webbrowser
import urllib.parse
import time
from pathlib import Path

class AuthService:
    """Microsoft authentication for Minecraft using vanilla launcher credentials"""
    
    def __init__(self):
        # Use the exact same credentials as the vanilla Minecraft launcher
        self.client_id = "00000000402b5328"
        self.redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        self.scopes = "XboxLive.signin offline_access"
        
        # Microsoft OAuth endpoints
        self.auth_url = "https://login.live.com/oauth20_authorize.srf"
        self.token_url = "https://login.live.com/oauth20_token.srf"
        
        self.auth_data_file = Path("auth_data.json")
        self.auth_data = self.load_auth_data()
    
    def load_auth_data(self):
        """Load saved authentication data"""
        try:
            if self.auth_data_file.exists():
                with open(self.auth_data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load auth data: {e}")
        return {}
    
    def save_auth_data(self, data):
        """Save authentication data"""
        try:
            with open(self.auth_data_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.auth_data = data
        except Exception as e:
            logging.error(f"Failed to save auth data: {e}")
    
    def authenticate(self):
        """Perform authentication using Microsoft device code flow (browser login, no QR code)"""
        try:
            if self.is_authenticated():
                logging.info("Using cached authentication")
                return True

            logging.info("Starting Microsoft device code authentication...")
            device_code_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
            data = {
                'client_id': self.client_id,
                'scope': self.scopes
            }
            resp = requests.post(device_code_url, data=data)
            if resp.status_code != 200:
                raise Exception(f"Failed to get device code: {resp.text}")
            device_data = resp.json()

            user_code = device_data['user_code']
            verification_uri = device_data['verification_uri']
            message = device_data.get('message')
            device_code = device_data['device_code']
            interval = device_data.get('interval', 5)

            print(f"\nTo sign in, go to {verification_uri} and enter the code: {user_code}\n")
            if message:
                print(message)

            # Open browser automatically
            try:
                webbrowser.open(verification_uri)
            except Exception as e:
                logging.warning(f"Could not open browser automatically: {e}")

            # Poll for token
            token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
            while True:
                time.sleep(interval)
                poll_data = {
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                    'client_id': self.client_id,
                    'device_code': device_code
                }
                poll_resp = requests.post(token_url, data=poll_data)
                if poll_resp.status_code == 200:
                    ms_token = poll_resp.json()
                    break
                err = poll_resp.json()
                if err.get('error') == 'authorization_pending':
                    continue
                elif err.get('error') == 'authorization_declined':
                    logging.error("Authorization was declined by the user.")
                    return False
                elif err.get('error') == 'expired_token':
                    logging.error("Device code expired. Please try again.")
                    return False
                elif err.get('error') == 'bad_verification_code':
                    logging.error("Invalid verification code.")
                    return False
                else:
                    logging.error(f"Device code error: {err}")
                    return False

            # Complete the authentication chain
            return self._complete_minecraft_auth(ms_token)
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return False
    
    def _create_auth_url(self):
        """Create Microsoft OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scopes,
            'prompt': 'select_account'
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"
    
    def _get_microsoft_token(self, auth_code):
        """Exchange authorization code for Microsoft access token"""
        data = {
            'client_id': self.client_id,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get Microsoft token: {response.text}")
        
        return response.json()
    
    def _complete_minecraft_auth(self, ms_token_data):
        """Complete the Minecraft authentication chain"""
        try:
            ms_access_token = ms_token_data['access_token']
            
            # Get Xbox Live token
            xbox_token = self._get_xbox_token(ms_access_token)
            if not xbox_token:
                return False
            
            # Get XSTS token
            xsts_data = self._get_xsts_token(xbox_token)
            if not xsts_data:
                return False
            
            # Get Minecraft token
            mc_token = self._get_minecraft_token(xsts_data)
            if not mc_token:
                return False
            
            # Get profile
            profile = self._get_minecraft_profile(mc_token)
            if not profile:
                return False
            
            # Save authentication data
            auth_data = {
                'ms_token': ms_token_data,
                'xbox_token': xbox_token,
                'xsts_data': xsts_data,
                'mc_token': mc_token,
                'profile': profile,
                'expires_at': time.time() + (ms_token_data.get('expires_in', 3600) - 300)  # 5 min buffer
            }
            
            self.save_auth_data(auth_data)
            logging.info(f"Successfully authenticated as {profile.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to complete Minecraft authentication: {e}")
            return False
    
    def _get_xbox_token(self, ms_access_token):
        """Get Xbox Live token"""
        try:
            data = {
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={ms_access_token}"
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT"
            }
            
            response = requests.post(
                'https://user.auth.xboxlive.com/user/authenticate',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['Token']
            
            logging.error(f"Xbox auth failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"Xbox token failed: {e}")
            return None
    
    def _get_xsts_token(self, xbox_token):
        """Get XSTS token"""
        try:
            data = {
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [xbox_token]
                },
                "RelyingParty": "rp://api.minecraftservices.com/",
                "TokenType": "JWT"
            }
            
            response = requests.post(
                'https://xsts.auth.xboxlive.com/xsts/authorize',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            
            logging.error(f"XSTS auth failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"XSTS token failed: {e}")
            return None
    
    def _get_minecraft_token(self, xsts_data):
        """Get Minecraft access token"""
        try:
            data = {
                "identityToken": f"XBL3.0 x={xsts_data['DisplayClaims']['xui'][0]['uhs']};{xsts_data['Token']}"
            }
            
            response = requests.post(
                'https://api.minecraftservices.com/authentication/login_with_xbox',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['access_token']
            
            logging.error(f"Minecraft auth failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"Minecraft token failed: {e}")
            return None
    
    def _get_minecraft_profile(self, mc_token):
        """Get Minecraft profile"""
        try:
            response = requests.get(
                'https://api.minecraftservices.com/minecraft/profile',
                headers={'Authorization': f'Bearer {mc_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            
            logging.error(f"Profile fetch failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logging.error(f"Profile fetch failed: {e}")
            return None
    
    def is_authenticated(self):
        """Check if user is authenticated with valid token"""
        if not self.auth_data:
            return False
        
        # Check if token is expired
        expires_at = self.auth_data.get('expires_at', 0)
        if time.time() >= expires_at:
            logging.info("Authentication token expired")
            return False
        
        # Check if we have all required data
        required_fields = ['mc_token', 'profile']
        return all(field in self.auth_data for field in required_fields)
    
    def get_minecraft_token(self):
        """Get the Minecraft access token"""
        if self.is_authenticated():
            return self.auth_data.get('mc_token')
        return None
    
    def get_profile(self):
        """Get the Minecraft profile"""
        if self.is_authenticated():
            return self.auth_data.get('profile')
        return None
    
    def get_auth_info(self):
        """Get authentication info for game launch"""
        if not self.is_authenticated():
            return None
        
        profile = self.get_profile()
        xsts_data = self.auth_data.get('xsts_data', {})
        
        return {
            'username': profile.get('name', 'Player'),
            'uuid': profile.get('id', ''),
            'access_token': self.get_minecraft_token(),
            'xuid': xsts_data.get('uhs', ''),  # Xbox User Hash from XSTS data
            'client_id': self.client_id
        }
    
    def logout(self):
        """Clear authentication data"""
        self.auth_data = {}
        try:
            if self.auth_data_file.exists():
                self.auth_data_file.unlink()
        except Exception as e:
            logging.warning(f"Failed to delete auth data file: {e}")
