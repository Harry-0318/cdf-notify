import requests
from datetime import datetime, timedelta
import dotenv
dotenv.load_dotenv()
import os
# -----------------------------
# Your Telegram info
# -----------------------------
BOT_TOKEN = os.getenv("ACCESS_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# -----------------------------
# Telegram notification function
# -----------------------------
def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# -----------------------------
# Get upcoming contests
# -----------------------------
def get_upcoming_contests():
    url = "https://codeforces.com/api/contest.list"
    response = requests.get(url).json()
    
    contests = []
    for contest in response['result']:
        if contest['phase'] == "BEFORE":
            contests.append({
                "name": contest['name'],
                "startTime": contest['startTimeSeconds'],
                "duration": contest['durationSeconds'],
                "id": contest['id']
            })
    return contests

# -----------------------------
# Check contests within 3 days
# -----------------------------
def notify_todays_contests():
    contests = get_upcoming_contests()
    now = datetime.utcnow()
    three_days_later = now + timedelta(days=3)
    
    found = False
    for contest in contests:
        start_time = datetime.utcfromtimestamp(contest['startTime'])
        if now <= start_time <= three_days_later:
            found = True
            contest_name = contest['name']
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            duration_hours = contest['duration'] // 3600
            duration_minutes = (contest['duration'] % 3600) // 60
            message = (
                f"🚨 Codeforces Contest Alert!\n\n"
                f"Contest: {contest_name}\n"
                f"Start Time: {start_str}\n"
                f"Duration: {duration_hours}h {duration_minutes}m"
            )
            send_telegram_message(BOT_TOKEN, CHAT_ID, message)
    
    if not found:
        send_telegram_message(BOT_TOKEN, CHAT_ID, "No Codeforces contests in the next 3 days.")

# -----------------------------
# Run the notifier
# -----------------------------
if __name__ == "__main__":
    notify_todays_contests()
