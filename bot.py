import os
import base64
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '').split(',')
OWNER_CHAT_ID = os.getenv('OWNER_CHAT_ID')
ALLOWED_GROUP_IDS = os.getenv('ALLOWED_GROUP_IDS', '').split(',')

GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_ENDPOINT = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

key_index = 0

def ask_gemini_text(prompt: str) -> str:
    global key_index
    for _ in range(len(GEMINI_API_KEYS)):
        key = GEMINI_API_KEYS[key_index].strip()
        url = f'{GEMINI_ENDPOINT}?key={key}'
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            data = response.json()
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in data:
                msg = data['error'].get('message', '')
                if 'quota' in msg.lower():
                    key_index = (key_index + 1) % len(GEMINI_API_KEYS)
                    continue
                return f"Gemini Error: {msg}"
        except Exception as e:
            return f"Request failed: {e}"
    return "All API keys failed or quota exceeded."

def ask_gemini_with_image(prompt: str, image_path: str) -> str:
    global key_index
    for _ in range(len(GEMINI_API_KEYS)):
        key = GEMINI_API_KEYS[key_index].strip()
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }]
            }

            response = requests.post(
                f"{GEMINI_ENDPOINT}?key={key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            data = response.json()
            if 'candidates' in data:
                return data['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in data:
                msg = data['error'].get('message', '')
                if 'quota' in msg.lower():
                    key_index = (key_index + 1) % len(GEMINI_API_KEYS)
                    continue
                return f"Gemini Error: {msg}"
        except Exception as e:
            return f"Request failed: {e}"
    return "All API keys failed or quota exceeded."

def handle_htet_text(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    if chat_id not in ALLOWED_GROUP_IDS:
        update.message.reply_text("🚧 This bot is only for allowed groups. Ask @Kamisama_HM to join.")
        return

    prompt = ' '.join(context.args).strip()
    if not prompt:
        update.message.reply_text("Usage: /htet <your prompt>")
        return

    update.message.reply_text("Processing prompt...")
    result = ask_gemini_text(prompt)
    update.message.reply_text(result)

def handle_htet_photo(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    if chat_id not in ALLOWED_GROUP_IDS:
        update.message.reply_text("🚧 This bot is only for allowed groups. Ask @Kamisama_HM to join.")
        return

    caption = update.message.caption or ""
    if not caption.startswith("/htet"):
        return

    prompt = caption.replace("/htet", "").strip() or "Describe this image"
    photos = update.message.photo
    if not photos:
        update.message.reply_text("No photo found.")
        return

    photo = photos[-1].get_file()
    image_path = os.path.join(DOWNLOAD_DIR, f"{photo.file_id}.jpg")
    photo.download(image_path)

    update.message.reply_text("Analyzing image...")
    result = ask_gemini_with_image(prompt, image_path)
    update.message.reply_text(result)

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("htet", handle_htet_text))
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.caption, handle_htet_photo))

    print("Bot is running... Send /htet or image with /htet caption.")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

