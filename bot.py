#!/usr/bin/env python3
import requests
import json
import time
import re
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
BOT_TOKEN = "8703034452:AAFvhGHuuNnO1kwUv0mWLqy1cyyNE6_uyaU"
POWER_BY = "@LEADER_JIIII"
ADMIN_ID = 7148414172  # Your admin user ID

# Instagram Download API
DOWNLOAD_API = "https://all-sigma-pad-api-damo-5-day.vercel.app/api?key=RAJAN123&type=DOWNLOAD&term={}"
# =================================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

# Data files
USERS_FILE = "users.json"
HISTORY_FILE = "history.json"

def load_data(filename, default):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return default

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# ============ HEALTH SERVER ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

# ============ TELEGRAM API ============
def send_msg(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"Send error: {response.status_code}")
        return response
    except Exception as e:
        print(f"Send error: {e}")
        return None

def send_video(chat_id, video_url, caption, reply_markup=None):
    url = f"{BASE_URL}/sendVideo"
    payload = {
        "chat_id": chat_id,
        "video": video_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"Video send error: {response.status_code}")
            # Try sending as document if video fails
            send_document(chat_id, video_url, caption, reply_markup)
        return response
    except Exception as e:
        print(f"Video send error: {e}")
        send_document(chat_id, video_url, caption, reply_markup)

def send_document(chat_id, file_url, caption, reply_markup=None):
    url = f"{BASE_URL}/sendDocument"
    payload = {
        "chat_id": chat_id,
        "document": file_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        requests.post(url, json=payload, timeout=60)
    except Exception as e:
        print(f"Document send error: {e}")

def send_typing(chat_id):
    url = f"{BASE_URL}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

# ============ KEYBOARDS ============
def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📥 DOWNLOAD REEL", "callback_data": "dl"}],
            [{"text": "👥 REFERRAL SYSTEM", "callback_data": "ref"}],
            [{"text": "📊 MY STATS", "callback_data": "stats"}],
            [{"text": "ℹ️ ABOUT", "callback_data": "about"}]
        ]
    }

def back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 BACK", "callback_data": "home"}]
        ]
    }

def ref_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📈 MY REFERRALS", "callback_data": "myrefs"}],
            [{"text": "🔙 BACK", "callback_data": "home"}]
        ]
    }

def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 STATS", "callback_data": "ad_stats"}],
            [{"text": "👥 USERS", "callback_data": "ad_users"}],
            [{"text": "📜 HISTORY", "callback_data": "ad_history"}],
            [{"text": "🔙 BACK", "callback_data": "home"}]
        ]
    }

# ============ DATA ============
def get_user(user_id):
    users = load_data(USERS_FILE, {})
    return users.get(str(user_id))

def save_user(user_id, username, name):
    users = load_data(USERS_FILE, {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "id": user_id,
            "username": username or name,
            "name": name,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": 0,
            "refs": 0
        }
        save_data(USERS_FILE, users)
        return True
    return False

def update_downloads(user_id):
    users = load_data(USERS_FILE, {})
    uid = str(user_id)
    if uid in users:
        users[uid]["downloads"] += 1
        save_data(USERS_FILE, users)

def add_history(user_id, username, url):
    history = load_data(HISTORY_FILE, [])
    history.append({
        "user_id": user_id,
        "username": username,
        "url": url,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(HISTORY_FILE, history[-100:])

def get_stats(user_id):
    u = get_user(user_id)
    if u:
        return f"""📊 YOUR STATS 📊

👤 Name: {u['name']}
🆔 Username: @{u['username']}

📥 Downloads: {u['downloads']}
👥 Referrals: {u['refs']}

📅 Joined: {u['joined']}

POWERED BY {POWER_BY}"""
    return "❌ No stats found. Please use /start first."

# ============ INSTAGRAM DOWNLOAD API ============
def extract_shortcode(url):
    """Extract Instagram shortcode from URL"""
    patterns = [
        r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)',
        r'instagram\.com/tv/([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_instagram_reel(url):
    """Fetch video URL from download API"""
    try:
        # Clean URL - remove query params
        clean_url = url.split('?')[0].rstrip('/')
        api_url = DOWNLOAD_API.format(clean_url)
        print(f"📡 API Call: {api_url}")
        
        resp = requests.get(api_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            
            # Extract video URL from response
            video_url = None
            
            # Check medias array
            if data.get("data", {}).get("data", {}).get("medias"):
                medias = data["data"]["data"]["medias"]
                if medias and len(medias) > 0:
                    video_url = medias[0].get("url")
            
            if not video_url and data.get("data", {}).get("video_url"):
                video_url = data["data"]["video_url"]
            
            if not video_url and data.get("video_url"):
                video_url = data["video_url"]
            
            if video_url:
                print(f"✅ Video found")
                return video_url
            else:
                print("❌ No video URL in response")
                return None
        else:
            print(f"❌ API HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ API Exception: {e}")
        return None

# ============ BOT HANDLERS ============
def handle_start(chat_id, user_id, name, username):
    save_user(user_id, username, name)
    
    msg = f"""🔥 WELCOME {name.upper()} 🔥

✨ Instagram Reel Download Bot ✨

✅ Fast & Free
✅ No Watermark  
✅ Referral System

📌 Send any Instagram Reel URL to download!

POWERED BY {POWER_BY}"""
    
    send_msg(chat_id, msg, main_keyboard())

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def handle_callback(chat_id, callback_id, data, message_id, user_id):
    if data == "home":
        send_msg(chat_id, "🔙 MAIN MENU", main_keyboard())
    
    elif data == "dl":
        send_msg(chat_id, f"📥 Send Instagram Reel URL\n\nExample: https://www.instagram.com/reel/xxxxx\n\nPOWERED BY {POWER_BY}", back_keyboard())
    
    elif data == "ref":
        bot_name = "Zyro_insta_bot"
        link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        u = get_user(user_id)
        ref_count = u["refs"] if u else 0
        
        msg = f"""✨ REFERRAL SYSTEM ✨

Your Referrals: {ref_count}

🔗 YOUR LINK:
{link}

Share this link with friends!

POWERED BY {POWER_BY}"""
        
        send_msg(chat_id, msg, ref_keyboard())
    
    elif data == "myrefs":
        u = get_user(user_id)
        msg = f"📈 YOUR REFERRALS\n\nTotal: {u['refs'] if u else 0}\n\nPOWERED BY {POWER_BY}"
        send_msg(chat_id, msg, back_keyboard())
    
    elif data == "stats":
        send_msg(chat_id, get_stats(user_id), back_keyboard())
    
    elif data == "about":
        msg = f"""🤖 INSTAGRAM REEL DOWNLOADER

✅ Download any Instagram Reel
✅ Fast & Free
✅ No Watermark
✅ Referral System

Bot: @Zyro_insta_bot
Creator: {POWER_BY}

POWERED BY {POWER_BY}"""
        send_msg(chat_id, msg, back_keyboard())
    
    # Admin callbacks
    elif is_admin(user_id):
        if data == "ad_stats":
            users = load_data(USERS_FILE, {})
            history = load_data(HISTORY_FILE, [])
            msg = f"""📊 ADMIN STATS

👥 Total Users: {len(users)}
📥 Total Downloads: {len(history)}

POWERED BY {POWER_BY}"""
            send_msg(chat_id, msg, admin_keyboard())
        
        elif data == "ad_users":
            users = load_data(USERS_FILE, {})
            txt = "👥 USERS LIST\n\n"
            for uid, data in list(users.items())[-20:]:
                txt += f"🆔 {uid}\n👤 @{data['username']}\n📥 {data['downloads']} downloads\n📅 {data['joined'][:10]}\n---\n"
            send_msg(chat_id, txt[:4000], admin_keyboard())
        
        elif data == "ad_history":
            history = load_data(HISTORY_FILE, [])
            txt = "📜 RECENT DOWNLOADS\n\n"
            for h in history[-20:]:
                txt += f"👤 @{h['username']}\n🔗 {h['url'][:50]}...\n🕐 {h['time'][:16]}\n---\n"
            send_msg(chat_id, txt[:4000], admin_keyboard())
    
    # Answer callback query
    url = f"{BASE_URL}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id, "text": "Processing..."})
    except:
        pass

def handle_message(chat_id, user_id, text_msg, username):
    url = text_msg.strip()
    
    # Check if Instagram URL
    if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
        send_msg(chat_id, f"❌ Send Instagram Reel URL only!\n\nExample: https://www.instagram.com/reel/xxxxx\n\nPOWERED BY {POWER_BY}", main_keyboard())
        return
    
    send_typing(chat_id)
    status = send_msg(chat_id, "🔄 Downloading... Please wait ⏳")
    
    video_url = download_instagram_reel(url)
    
    if video_url:
        update_downloads(user_id)
        add_history(user_id, username, url)
        
        cap = f"✅ Reel Ready!\n\nPOWERED BY {POWER_BY}"
        
        try:
            send_video(chat_id, video_url, cap, main_keyboard())
        except:
            send_msg(chat_id, f"📥 Download Link: {video_url}\n\nPOWERED BY {POWER_BY}", main_keyboard())
    else:
        send_msg(chat_id, f"❌ Failed to download! Try another reel or check the link.\n\nPOWERED BY {POWER_BY}", main_keyboard())

def handle_admin_command(chat_id, user_id, text):
    if not is_admin(user_id):
        send_msg(chat_id, "❌ Unauthorized! You are not admin.")
        return
    
    if text == "/admin" or text == "/Admin":
        msg = "🔐 ADMIN PANEL\n\nWelcome Admin!\n\nUse buttons below:"
        send_msg(chat_id, msg, admin_keyboard())
    
    elif text == "/stats":
        users = load_data(USERS_FILE, {})
        history = load_data(HISTORY_FILE, [])
        msg = f"""📊 ADMIN STATS

👥 Users: {len(users)}
📥 Downloads: {len(history)}

POWERED BY {POWER_BY}"""
        send_msg(chat_id, msg)
    
    elif text == "/users":
        users = load_data(USERS_FILE, {})
        txt = "👥 USERS LIST\n\n"
        for uid, data in list(users.items())[-20:]:
            txt += f"🆔 {uid}\n👤 @{data['username']}\n📥 {data['downloads']}\n📅 {data['joined'][:10]}\n---\n"
        send_msg(chat_id, txt[:4000])

# ============ MAIN LOOP ============
def handle_update(update):
    global OFFSET
    
    if "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat", {}).get("id", 0)
        text = msg.get("text", "")
        user_id = msg.get("from", {}).get("id", 0)
        username = msg.get("from", {}).get("username", "")
        name = msg.get("from", {}).get("first_name", "User")
        
        print(f"📨 Message from {user_id}: {text[:50]}")
        
        if text == "/start":
            # Check for referral
            ref_by = None
            if len(text.split()) > 1:
                ref_part = text.split()[1]
                if ref_part.startswith("ref_"):
                    try:
                        ref_by = int(ref_part.split("_")[1])
                        if ref_by == user_id:
                            ref_by = None
                    except:
                        pass
            handle_start(chat_id, user_id, name, username)
        
        elif text.startswith("/admin") or text.startswith("/Admin"):
            handle_admin_command(chat_id, user_id, text)
        
        elif text.startswith("/stats") or text.startswith("/users"):
            handle_admin_command(chat_id, user_id, text)
        
        elif text.startswith("/"):
            send_msg(chat_id, "❌ Unknown command! Use /start to begin.")
        
        else:
            handle_message(chat_id, user_id, text, username)
    
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback.get("message", {}).get("chat", {}).get("id", 0)
        callback_id = callback.get("id", "")
        data = callback.get("data", "")
        user_id = callback.get("from", {}).get("id", 0)
        message_id = callback.get("message", {}).get("message_id", 0)
        
        print(f"📨 Callback from {user_id}: {data}")
        handle_callback(chat_id, callback_id, data, message_id, user_id)

def main():
    # Initialize files
    load_data(USERS_FILE, {})
    load_data(HISTORY_FILE, [])
    
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 50)
    print("🤖 INSTAGRAM REEL DOWNLOADER BOT")
    print(f"👨‍💻 Powered by: {POWER_BY}")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print("=" * 50)
    
    global OFFSET
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/getUpdates", 
                               params={"offset": OFFSET, "timeout": 30}, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        handle_update(update)
                        OFFSET = update.get("update_id", OFFSET) + 1
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
