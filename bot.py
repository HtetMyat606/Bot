import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from keep_alive import keep_alive
keep_alive()


# Load tokens from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_URL = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key={GEMINI_API_KEY}'

def ask_gemini(prompt: str) -> str:
    try:
        response = requests.post(
            GEMINI_URL,
            headers={'Content-Type': 'application/json'},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        data = response.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
        elif 'error' in data:
            return f"Gemini Error: {data['error']['message']}"
        return "No valid response received from Gemini."
    except Exception as e:
        return f"Request failed: {e}"

def handle_htet(update: Update, context: CallbackContext) -> None:
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
