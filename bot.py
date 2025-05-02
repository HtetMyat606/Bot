import os
import requests
import hashlib
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from keep_alive import keep_alive
from diskcache import Cache

keep_alive()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OWNER_CHAT_ID = os.getenv('OWNER_CHAT_ID')  # Optional: set your Telegram user ID here

GEMINI_URL = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key={GEMINI_API_KEY}'

cache = Cache(".cache")

last_request_time = 0
RATE_LIMIT_SECONDS = 10

def get_cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def is_rate_limited() -> bool:
    global last_request_time
    now = time.time()
    if now - last_request_time < RATE_LIMIT_SECONDS:
        return True
    last_request_time = now
    return False

def log(message: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def notify_owner(context: CallbackContext, text: str):
    if OWNER_CHAT_ID:
        context.bot.send_message(chat_id=int(OWNER_CHAT_ID), text=f"Bot Alert:\n{text}")

def ask_gemini(prompt: str, context: CallbackContext = None) -> str:
    key = get_cache_key(prompt)

    if key in cache:
        log(f"Cache hit for: {prompt}")
        return cache[key]

    try:
        log(f"Sending to Gemini: {prompt}")
        response = requests.post(
            GEMINI_URL,
            headers={'Content-Type': 'application/json'},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        data = response.json()
        if 'candidates' in data:
            result = data['candidates'][0]['content']['parts'][0]['text']
            cache[key] = result
            return result
        elif 'error' in data:
            error_msg = f"Gemini Error: {data['error']['message']}"
            log(error_msg)
            if context:
                notify_owner(context, error_msg)
            return error_msg
        return "No valid response received from Gemini."
    except Exception as e:
        err = f"Request failed: {e}"
        log(err)
        if context:
            notify_owner(context, err)
        return err

def handle_htet(update: Update, context: CallbackContext) -> None:
    user_input = ' '.join(context.args)
    if not user_input:
        update.message.reply_text("Usage: /htet <your message>")
        return

    if is_rate_limited():
        update.message.reply_text("Please wait a few seconds before sending another request.")
        return

    reply = ask_gemini(user_input, context)
    update.message.reply_text(reply)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("htet", handle_htet))
    print("Bot is running... (Use /htet)")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    
