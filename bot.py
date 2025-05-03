import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
keep_alive()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '').split(',')
OWNER_CHAT_ID = os.getenv('OWNER_CHAT_ID')
ALLOWED_GROUP_IDS = os.getenv('ALLOWED_GROUP_IDS', '').split(',')

# Track current key index
key_index = 0

def ask_gemini(prompt: str) -> str:
    global key_index
    for _ in range(len(GEMINI_API_KEYS)):
        key = GEMINI_API_KEYS[key_index].strip()
        url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key={key}'
        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=10
            )
            data = response.json()
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in data and 'quota' in data['error'].get('message', '').lower():
                key_index = (key_index + 1) % len(GEMINI_API_KEYS)
                continue  # Try next key
            elif 'error' in data:
                return f"Gemini Error: {data['error']['message']}"
        except Exception as e:
            return f"Request failed: {e}"
    return "All Gemini API keys have reached their limits or failed."

def handle_htet(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    if chat_id not in ALLOWED_GROUP_IDS:
        update.message.reply_text("This bot will only work in GROUP 1")
        return  # Ignore messages from unauthorized chats

    user_input = ' '.join(context.args)
    if not user_input:
        update.message.reply_text("Usage: /htet <your message>")
        return

    reply = ask_gemini(user_input)
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
