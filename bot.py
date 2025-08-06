import os
import json
import time
import logging
import requests
from pathlib import Path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ======================== تنظیمات ========================
OWNER_ID = 7447486443
OFFLINE_FILE = "offline_state.json"
INTRO_TRACK_FILE = "intro_timestamps.json"
MEMORY_FILE = "user_memory.json"
INTRO_INTERVAL = 3600
MEMORY_EXPIRATION = 3600
OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
# ========================================================

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).exists() else {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

offline_state = load_json(OFFLINE_FILE)
intro_timestamps = load_json(INTRO_TRACK_FILE)
user_memory = load_json(MEMORY_FILE)

def is_offline():
    return offline_state.get("status") == "offline"

def set_offline():
    offline_state["status"] = "offline"
    save_json(OFFLINE_FILE, offline_state)

def set_online():
    offline_state["status"] = "online"
    save_json(OFFLINE_FILE, offline_state)

def ask_openrouter(prompt, user_id):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    user_history = user_memory.get(str(user_id), [])
    user_history = [m for m in user_history if time.time() - m["time"] < MEMORY_EXPIRATION]

    messages = [{"role": "system", "content": "تو یک دستیار فارسی‌زبان، شوخ، خودمونی و صمیمی هستی که فقط فارسی جواب می‌ده."}]
    messages += [{"role": "user", "content": m["text"]} for m in user_history]
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "openchat/openchat-7b:free",
        "messages": messages
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        user_history.append({"text": prompt, "time": time.time()})
        user_memory[str(user_id)] = user_history
        save_json(MEMORY_FILE, user_memory)
        return content
    except Exception:
        return "خطا در ارتباط با هوش مصنوعی 🛠️"

def should_send_intro(user_id):
    now = time.time()
    last = intro_timestamps.get(str(user_id), 0)
    if now - last >= INTRO_INTERVAL:
        intro_timestamps[str(user_id)] = now
        save_json(INTRO_TRACK_FILE, intro_timestamps)
        return True
    return False

def handle_message(update, context):
    msg = update.effective_message
    user = update.effective_user

    if not is_offline():
        return

    if should_send_intro(user.id):
        msg.reply_text(
            "👀 نادم الان نیست که بخواد باهات صحبت کنه...\n"
            "📡 اما نگران نباش! من دستیار هوش مصنوعی نادمم 😎\n"
            "وظیفه‌م اینه تا وقتی آقا خودش برگشت، حواسم به همه چی باشه!\n\n"
            "🧠 اگه سوالی داری، همین حالا بپرس تا راهنماییت کنم."
        )

    text = msg.text or ""

    lowered = text.lower()
    if "ندم" in lowered:
        msg.reply_text("نادم نه عزیز دل، نـ ــادم 😅")
        return
    if "نادم" in lowered:
        msg.reply_text("نادم؟ 😎 خالق من و آقابالاسرمه! فعلاً که خودش نیست ولی من مراقبم!")
        return
    if "یادت نیست" in lowered or "یادش نیستی" in lowered or "چرا یادت نمی‌مونه" in lowered:
        msg.reply_text("🧠 من هر ۱ ساعت حافظه‌م پاک میشه 😅 برای همین چیزایی که گفتی یادم نمی‌مونه!")
        return

    if msg.text:
        reply = ask_openrouter(msg.text, user.id)
        msg.reply_text(reply)
    else:
        msg.reply_text("پیامتو دیدم 😄 هر چی با متن بهم بگی بهتر می‌تونم راهنماییت کنم!")

def go_offline(update, context):
    if update.effective_user.id == OWNER_ID:
        set_offline()
        update.message.reply_text("🟠 نادم آفلاین شد. من مراقبم 😎")

def go_online(update, context):
    if update.effective_user.id == OWNER_ID:
        set_online()
        update.message.reply_text("🟢 نادم آنلاین شد. دیگه من سکوت می‌کنم 😇")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("offline", go_offline))
    dp.add_handler(CommandHandler("online", go_online))
    dp.add_handler(MessageHandler(Filters.all, handle_message))

    updater.start_polling()
    logging.info("🤖 ربات راه‌اندازی شد و منتظر پیام‌هاست...")
    updater.idle()

if __name__ == "__main__":
    main()
