import re
import os
from dotenv import load_dotenv

load_dotenv()

def parse_cookies(cookie_str):
    cookies = {}
    for line in cookie_str.strip().split('\n'):
        if line.startswith(('#', '//')) or not line.strip():
            continue
        parts = re.split(r'\s+', line)
        if len(parts) >= 7 and not parts[0].startswith('.'):
            cookies[parts[5]] = parts[6]
    return cookies

class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID", "25331263"))
    API_HASH = os.getenv("API_HASH", "cab85305bf85125a2ac053210bcd1030")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8120224293:AAEQ4O2sm-ci0YCobS0DD7NSOD_UdjxNAOU")
    OWNER_ID = [int(x) for x in os.getenv("OWNER_ID", "1955406483").split()]
    
    # Database
    MONGO_DB = os.getenv("MONGO_DB", "mongodb+srv://rs92573993688:pVf4EeDuRi2o92ex@cluster0.9u29q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
    # Channels
    LOG_GROUP = int(os.getenv("LOG_GROUP", "-1002584826508"))
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002888391802"))
    
    # Limits
    FREEMIUM_LIMIT = int(os.getenv("FREEMIUM_LIMIT", "10"))
    PREMIUM_LIMIT = int(os.getenv("PREMIUM_LIMIT", "10000"))
    WEBSITE_URL = os.getenv("WEBSITE_URL", "https://your-website.com")
    
    # Cookies (VPS deployment)
    INST_COOKIES = parse_cookies(os.getenv("INST_COOKIES", """
        .instagram.com	TRUE	/	TRUE	1785372024	csrftoken	L64ejzKhtYTqxVmSBOC4XqY9V4bhxLxu
        .instagram.com	TRUE	/	TRUE	1785371887	datr	8ERbaIVkujFC8tioGF1TVRJ4
        .instagram.com	TRUE	/	TRUE	1782347887	ig_did	49AB89A9-CD57-487F-B6E0-EF845E1E0BDF
        .instagram.com	TRUE	/	TRUE	1751416830	wd	360x696
        .instagram.com	TRUE	/	TRUE	1751416814	dpr	2
        .instagram.com	TRUE	/	TRUE	1785371891	mid	aFtE8AABAAEetqneMGwVLPDirCt4
        .instagram.com	TRUE	/	TRUE	1758588024	ds_user_id	75604963433
        .instagram.com	TRUE	/	TRUE	1782348014	sessionid	75604963433%3AJjczfDiVSXHw4P%3A7%3AAYeMtcqjXx5bLJCoI6bPZkYdL_LXmQ69DHQC7vkIaQ
    """))
    
    YTUB_COOKIES = parse_cookies(os.getenv("YTUB_COOKIES", """
        .youtube.com	TRUE	/	TRUE	1765985720	__Secure-ROLLOUT_TOKEN	CKzpktuYyuW-9gEQuf-_4amAjgMYwqDc4amAjgM%3D
        .youtube.com	TRUE	/	TRUE	1765985775	VISITOR_INFO1_LIVE	E-mL-YXFbaE
        .youtube.com	TRUE	/	TRUE	1765985775	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgYQ%3D%3D
        .youtube.com	TRUE	/	TRUE	1750435520	GPS	1
        .youtube.com	TRUE	/	TRUE	1784993775	PREF	f6=40000000&tz=Asia.Kolkata
        .google.com	TRUE	/	TRUE	1784993746	__Secure-1PSID	g.a000yQgqdVm5DKNNAXLyukGZzV5tznWx1jn-DsDAXsX4A8vooEL63zqLvNQmAXGXG7kZ5z9qdAACgYKAQkSARASFQHGX2Mip9uDusvqvNSNO4nxBYl2cxoVAUF8yKqAFFhKIP66nFCPY-NF4IAx0076
        .youtube.com	TRUE	/	TRUE	1781969773	__Secure-1PSIDTS	sidts-CjEB5H03P12p_7RzZmTeYAe7B__kP8lToK8iISgbjcuiLKnX4E5KiRgmd66osdUzQvjqEAA
    """))
    
    # Validate critical cookies
    if not INST_COOKIES.get("sessionid"):
        raise ValueError("Instagram sessionid cookie missing! Account login required.")
    if not YTUB_COOKIES.get("__Secure-1PSID"):
        raise ValueError("YouTube __Secure-1PSID cookie missing! Login required.")

config = Config()
