import json
import os
import time
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from curl_cffi import requests # 使用 curl_cffi 绕过 TLS 指纹识别

# 尝试导入 ddddocr
try:
    import ddddocr
    HAS_DDDDOCR = True
except ImportError:
    HAS_DDDDOCR = False

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sessions')
JSL_SESSION_FILE = os.path.join(SESSION_DIR, 'jsl_session.json')

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

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
        self.session = requests.Session(impersonate="chrome110")
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.jisilu.cn/account/login/"
        })

    def is_logged_in(self) -> bool:
        try:
            # 访问首页检查是否有“退出”
            res = self.session.get("https://www.jisilu.cn/", timeout=10)
            if "退出" in res.text:
                return True
            return False
        except Exception as e:
            print(f"[DEBUG] 检查登录状态异常: {e}")
            return False

    def get_captcha(self):
        """获取验证码内容"""
        if not HAS_DDDDOCR:
            print("[WARNING] 未检测到 ddddocr 库，无法自动识别验证码。请运行 'pip install ddddocr'。")
            return None
        
        try:
            # 这里的 URL 需要根据集思录实际情况，通常是 captcha 接口
            captcha_url = f"https://www.jisilu.cn/account/captcha/?{int(time.time()*1000)}"
            res = self.session.get(captcha_url, timeout=10)
            
            ocr = ddddocr.DdddOcr(show_ad=False)
            res_text = ocr.classification(res.content)
            print(f"[INFO] 验证码自动识别结果: {res_text}")
            return res_text
        except Exception as e:
            print(f"[ERROR] 获取验证码失败: {e}")
            return None

    def login(self, force=False):
        # 1. 尝试加载现有 Cookie
        if not force and os.path.exists(JSL_SESSION_FILE):
            try:
                with open(JSL_SESSION_FILE, 'r') as f:
                    data = json.load(f)
                # 使用 curl_cffi 的方式设置 cookie
                cookie_dict = data.get('cookies', {})
                for k, v in cookie_dict.items():
                    self.session.cookies.set(k, v)
                
                if self.is_logged_in():
                    print("[INFO] 集思录已通过 Cookie 登录成功")
                    return True
                else:
                    print("[INFO] Cookie 已失效，将尝试重新登录")
            except Exception as e:
                print(f"[DEBUG] 加载 Cookie 失败: {e}")

        # 2. 账号密码登录
        if not self.username or not self.password:
            print("[ERROR] 未配置 JISILU_USERNAME 或 JISILU_PASSWORD")
            return False
        
        print(f"[INFO] 正在尝试登录账号: {self.username}")
        
        # 先访问登录页获取基础 Cookie
        self.session.get("https://www.jisilu.cn/account/login/")
        
        # 构造登录请求
        login_url = "https://www.jisilu.cn/webapi/account/login_process/"
        payload = {
            "user_name": jsl_aes_encrypt(self.username),
            "password": jsl_aes_encrypt(self.password),
            "return_url": "https://www.jisilu.cn/",
            "auto_login": "1",
            "aes": "1"
        }

        # 尝试第一次登录（不带验证码）
        res = self.session.post(login_url, data=payload)
        res_data = {}
        try:
            res_data = res.json()
        except:
            pass

        # 如果需要验证码或者登录失败，尝试带验证码再次登录
        if res_data.get('errno') != 0:
            seccode = self.get_captcha()
            if seccode:
                payload["seccode_verify"] = seccode
                # 重新请求
                res = self.session.post(login_url, data=payload)
                try:
                    res_data = res.json()
                except:
                    pass

        # 最终校验
        if res_data.get('errno') == 0 or res_data.get('status') == 'ok' or self.is_logged_in():
            print("[SUCCESS] 集思录登录成功！")
            # 保存新 Cookie
            with open(JSL_SESSION_FILE, 'w') as f:
                # 获取字典格式的 cookies
                cookies = {}
                for k, v in self.session.cookies.items():
                    cookies[k] = v
                json.dump({'cookies': cookies, 'timestamp': time.time()}, f)
            return True
        else:
            print(f"[ERROR] 登录失败: {res_data}")
            return False

    def get_session(self) -> requests.Session:
        return self.session

jsl_session_manager = JisiluSession()

def get_jsl_session():
    # 每次获取前，如果内存中的 session 未登录，则尝试登录（优先使用本地 Cookie）
    if not jsl_session_manager.is_logged_in():
        jsl_session_manager.login(force=False)
    return jsl_session_manager.get_session()
