# -*- coding: utf-8 -*-
import logging
from telegram import Update, Message, ChatAction
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext
import requests
import time
import re

# توکن رباتت
BOT_TOKEN = "7977751221:AAHBPEXCseUUdFIqX0Tumw7lqzxVR_Mz7LM"
OPENROUTER_API_KEY = "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"

OWNER_ID = 736052064
user_memory = {}  # حافظه چت یک ساعته
welcome_shown = {}  # پیغام خوشامد ۶ ساعته
MEMORY_TIMEOUT = 3600
WELCOME_INTERVAL = 6 * 3600

# تنظیمات لاگ برای نمایش پیام‌های مهم در ترمینال
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# وضعیت آنلاین/آفلاین
is_owner_online = False

# دستور آنلاین شدن
def go_online(update: Update, context: CallbackContext):
    global is_owner_online
    if update.effective_user.id == OWNER_ID:
        is_owner_online = True
        update.message.reply_text("✅ نادم آنلاین شد.")

# دستور آفلاین شدن
def go_offline(update: Update, context: CallbackContext):
    global is_owner_online
    if update.effective_user.id == OWNER_ID:
        is_owner_online = False
        update.message.reply_text("🟠 نادم آفلاین شد.")

# بررسی فارسی بودن متن
def is_persian(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

# پاسخ از OpenRouter (GPT)
def ask_ai(prompt, user_id):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": "تو دستیار نادم هستی. لحن خودمونی و با ایموجی داشته باش."}]
    
    # اضافه‌کردن حافظه گفتگو (اگر وجود داشته باشه)
    if user_id in user_memory:
        for old in user_memory[user_id]["history"][-6:]:
            messages.append({"role": "user", "content": old})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        reply = res.json()["choices"][0]["message"]["content"]
        return reply.strip()
    except:
        return "😓 یه مشکلی پیش اومد موقع گرفتن پاسخ. یه بار دیگه بپرس."

# پاسخ‌های آماده
def check_special_messages(text):
    if "تو کی" in text or "نادم کیه" in text or "مالک" in text:
        return "👤 نادم یه آدم گمنام ولی باهوشه که دنبال آگاه‌سازی مردمه. من دستیار هوش مصنوعی‌شم! 😎"
    if "یادت نیست" in text or "فراموش" in text:
        return "🧠 حافظه من هر ۱ ساعت یه بار پاک میشه عزیز! اگه یادت نیست دلیلش اینه 😅"
    return None

# پیام‌های غیر متنی
def handle_other_formats(update: Update, context: CallbackContext):
    msg = update.effective_message
    msg.reply_text("🎬📸🎤 اوه! این فرمتو نمی‌تونم تحلیل کنم.\nفقط با متن کار می‌کنم فعلاً 😅")

# پیام متنی
def handle(update: Update, context: CallbackContext):
    global is_owner_online

    user_id = update.effective_user.id
    msg = update.message
    text = msg.text or ""

    if update.effective_user.id == OWNER_ID:
        return  # به خودت جواب نده

    if is_owner_online:
        return  # نادم آنلاین باشه، جوابی نده

    now = time.time()

    # نشون دادن پیام خوشامد فقط هر ۶ ساعت
    if user_id not in welcome_shown or now - welcome_shown[user_id] > WELCOME_INTERVAL:
        msg.reply_text(
            "👀 نادم الان نیست که بخواد باهات صحبت کنه...\n"
            "📡 اما نگران نباش! من دستیار هوش مصنوعی نادمم 😎\n"
            "وظیفه‌م اینه تا وقتی آقا خودش برگشت، حواسم به همه چی باشه!\n\n"
            "🧠 اگه سوالی داری، همین حالا بپرس تا راهنماییت کنم."
        )
        welcome_shown[user_id] = now

    # فقط پیام فارسی رو جواب بده
    if not is_persian(text):
        msg.reply_text("😅 فقط می‌تونم فارسی جواب بدم. یه بار دیگه با حروف فارسی بپرس لطفاً!")
        return

    # پاسخ‌های خاص
    static_reply = check_special_messages(text)
    if static_reply:
        msg.reply_text(static_reply)
        return

    # ذخیره‌سازی در حافظه
    if user_id not in user_memory or now - user_memory[user_id]["time"] > MEMORY_TIMEOUT:
        user_memory[user_id] = {"history": [], "time": now}
    user_memory[user_id]["history"].append(text)
    user_memory[user_id]["time"] = now

    # نشون دادن وضعیت تایپ
    context.bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)

    # گرفتن پاسخ
    reply = ask_ai(text, user_id)
    msg.reply_text(reply)

# اجرای اصلی
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("online", go_online))
    dp.add_handler(CommandHandler("offline", go_offline))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    dp.add_handler(MessageHandler(~Filters.text, handle_other_formats))

    updater.start_polling()
    logging.info("✅ ربات راه‌اندازی شد و آماده پاسخ‌گویی‌ه 😎")
    updater.idle()

if __name__ == '__main__':
    main()
