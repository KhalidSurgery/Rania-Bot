import openai
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# تعريف الحالات في المحادثة
CHAT, END_CHAT = range(2)

# متغيرات البيئة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = f"{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_BOT_TOKEN}"

# دالة الاتصال بـ GPT
def ask_gpt_rania(user_input):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "مرحبًا! أنا رانية..."}, {"role": "user", "content": user_input}]
    )
    return response["choices"][0]["message"]["content"]

# إرسال إشعار واتساب
def send_whatsapp_message(name, phone, chat_summary):
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}\n📌 ملخص المحادثة: {chat_summary}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء المحادثة
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا! أنا رانية، مساعدتك الافتراضية...")
    return CHAT

# استقبال الرسائل
def chat(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    response = ask_gpt_rania(user_input)
    update.message.reply_text(response)
    return CHAT

# إنهاء المحادثة
def end_chat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم إنهاء المحادثة، شكرًا لك!")
    return END_CHAT

# إعداد البوت
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CHAT: [MessageHandler(Filters.text & ~Filters.command, chat)], END_CHAT: [CommandHandler("end", end_chat)]},
        fallbacks=[CommandHandler("end", end_chat)],
    )

    dp.add_handler(conv_handler)

    # 🔹 ضبط Webhook بشكل صحيح
updater.start_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8443)),
    url_path=TELEGRAM_BOT_TOKEN
)
updater.bot.setWebhook(f"https://rania-bot.onrender.com/{TELEGRAM_BOT_TOKEN}")

updater.idle()  # تأكد أن هذه في نفس المستوى


if __name__ == "__main__":
    main()
