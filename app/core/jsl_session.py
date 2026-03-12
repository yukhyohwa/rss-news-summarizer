import requests
import json
import os
import time
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions')
JSL_SESSION_FILE = os.path.join(SESSION_DIR, 'jsl_session.json')

def jsl_aes_encrypt(text: str) -> str:
    key = b'397151C04723421F'
    cipher = AES.new(key, AES.MODE_ECB)
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.jisilu.cn/account/login/"
        })

    def is_logged_in(self) -> bool:
        try:
            # 访问一个极小的私有接口验证
            res = self.session.get("https://www.jisilu.cn/invite/", timeout=10)
            return "邀请" in res.text and "登录" not in res.text
        except:
            return False

    def login(self):
        # 1. 尝试加载
        if os.path.exists(JSL_SESSION_FILE):
            with open(JSL_SESSION_FILE, 'r') as f:
                data = json.load(f)
            self.session.cookies.update(data.get('cookies', {}))
            if self.is_logged_in():
                print("[INFO] 集思录已自动通过 Cookie 登录")
                return True

        # 2. 账号登录
        if not self.username: return False
        
        print(f"[INFO] 正在尝试登录账号: {self.username}")
        # 获取基础 Cookie
        self.session.get("https://www.jisilu.cn/account/login/")
        
        # 集思录目前有两种登录路径，我们尝试更通用的 webapi
        login_url = "https://www.jisilu.cn/webapi/account/login_process/"
        payload = {
            "user_name": jsl_aes_encrypt(self.username),
            "password": jsl_aes_encrypt(self.password),
            "return_url": "https://www.jisilu.cn/",
            "auto_login": "1",
            "aes": "1"
        }
        
        res = self.session.post(login_url, data=payload)
        try:
            res_data = res.json()
            if res_data.get('errno') == 0 or res_data.get('status') == 'ok':
                print("[SUCCESS] 登录成功！")
                with open(JSL_SESSION_FILE, 'w') as f:
                    json.dump({'cookies': self.session.cookies.get_dict(), 'timestamp': time.time()}, f)
                return True
            else:
                print(f"[ERROR] 登录失败详请: {res_data}")
        except:
            print(f"[ERROR] 登录响应格式错误: {res.text[:100]}")
        
        return False

    def get_session(self) -> requests.Session:
        return self.session

jsl_session_manager = JisiluSession()

def get_jsl_session():
    jsl_session_manager.login()
    return jsl_session_manager.get_session()
