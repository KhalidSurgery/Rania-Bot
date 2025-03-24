import asyncio
import os
import openai
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# تعريف الحالات في المحادثة
CHAT, END_CHAT = range(2)

# جلب مفاتيح API من متغيرات البيئة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# التحقق من المفاتيح
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables")

# الاتصال بـ OpenAI
def ask_gpt_rania(user_input):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "مرحبًا! أنا رانية، مساعدتك الافتراضية في عيادة الدكتور خالد حسون."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

# إرسال إشعار واتساب
def send_whatsapp_message(name, phone, chat_summary):
    if not WHATSAPP_NUMBER or not CALLMEBOT_API_KEY:
        return  # تجنب الخطأ إذا لم تكن القيم محددة
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}\n📌 ملخص المحادثة: {chat_summary}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء المحادثة
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("مرحبًا! أنا رانية، مساعدتك الافتراضية...")
    return CHAT

# استقبال الرسائل
async def chat(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    response = ask_gpt_rania(user_input)
    await update.message.reply_text(response)
    return CHAT

# إنهاء المحادثة
async def end_chat(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("تم إنهاء المحادثة، شكرًا لك!")
    return ConversationHandler.END

# تشغيل البوت
def main():
    # استخدام get_event_loop() بدلاً من asyncio.run()
    loop = asyncio.get_event_loop()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[CommandHandler('end', end_chat)]
    )
    
    application.add_handler(conv_handler)
    
    try:
        # استخدام run_forever بدلاً من run_polling
        loop.run_until_complete(application.run_polling())
    except KeyboardInterrupt:
        # التعامل مع إيقاف البرنامج
        print("تم إيقاف البوت")
    finally:
        # إغلاق التطبيق بشكل آمن
        loop.run_until_complete(application.stop())

if __name__ == "__main__":
    main()
