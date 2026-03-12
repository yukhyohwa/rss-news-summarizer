import requests
import json
import os
import time
from typing import Optional, Dict
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Path for session storage
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions')
JSL_SESSION_FILE = os.path.join(SESSION_DIR, 'jsl_session.json')

def jsl_aes_encrypt(text: str) -> str:
    """Implement Jisilu's client-side AES encryption."""
    key = b'397151C04723421F'
    cipher = AES.new(key, AES.MODE_ECB)
    # Pkcs7 padding
    padded_data = pad(text.encode('utf-8'), AES.block_size, style='pkcs7')
    encrypted = cipher.encrypt(padded_data)
    return encrypted.hex()

class JisiluSession:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('JISILU_USERNAME')
        self.password = os.getenv('JISILU_PASSWORD')
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.jisilu.cn",
            "Referer": "https://www.jisilu.cn/account/login/"
        })
        
        if not os.path.exists(SESSION_DIR):
            os.makedirs(SESSION_DIR)

    def _save_session(self):
        """Save cookies to a file."""
        cookies = self.session.cookies.get_dict()
        with open(JSL_SESSION_FILE, 'w') as f:
            json.dump({'cookies': cookies, 'timestamp': time.time()}, f)

    def _load_session(self) -> bool:
        """Load cookies from a file if they exist and aren't too old (e.g., 7 days)."""
        if not os.path.exists(JSL_SESSION_FILE):
            return False
            
        try:
            with open(JSL_SESSION_FILE, 'r') as f:
                data = json.load(f)
                
            # Check if session is older than 7 days
            if time.time() - data.get('timestamp', 0) > 7 * 24 * 3600:
                return False
                
            self.session.cookies.update(data.get('cookies', {}))
            return True
        except Exception:
            return False

    def login(self) -> bool:
        """Login to Jisilu using AES encryption and save session."""
        if not self.username or not self.password:
            print("[WARN] Jisilu credentials not found in .env. Running as guest.")
            return False

        # Try to load existing session first
        if self._load_session():
            # Quick check if session is still valid (using a small data request)
            test_url = "https://www.jisilu.cn/data/lof/index_lof_list/?rp=1"
            try:
                res = self.session.get(test_url, timeout=10)
                if res.status_code == 200 and '"rows"' in res.text:
                    print("[INFO] Jisilu session loaded and verified.")
                    return True
            except Exception:
                pass

        print("[INFO] Jisilu session invalid or missing. Attempting login...")
        # New WebAPI endpoint
        login_url = "https://www.jisilu.cn/webapi/account/login_process/"
        
        try:
            # Encrypt credentials as required by Jisilu
            enc_user = jsl_aes_encrypt(self.username)
            enc_pass = jsl_aes_encrypt(self.password)
            
            payload = {
                "return_url": "https://www.jisilu.cn/",
                "user_name": enc_user,
                "password": enc_pass,
                "auto_login": "1",
                "aes": "1"
            }
            
            # First hit the login page to get initial cookies
            self.session.get("https://www.jisilu.cn/account/login/")
            
            # Post encrypted login data
            response = self.session.post(login_url, data=payload)
            res_json = response.json()
            
            # Jisilu API returns status 'ok' or 'error'
            if res_json.get('status') == 'ok' or res_json.get('errno') == 0:
                print("[SUCCESS] Jisilu logged in successfully.")
                self._save_session()
                return True
            else:
                err_msg = res_json.get('err') or res_json.get('msg') or "Unknown error"
                print(f"[ERROR] Jisilu login failed: {err_msg}")
                return False
        except Exception as e:
            print(f"[ERROR] Jisilu login exception: {e}")
            return False

    def get_session(self) -> requests.Session:
        """Get the active session object."""
        return self.session

# Singleton instance
jsl_session_manager = JisiluSession()

def get_jsl_session():
    """Helper to ensure we are logged in and return the session."""
    jsl_session_manager.login()
    return jsl_session_manager.get_session()
