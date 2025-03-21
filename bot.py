import openai  # مكتبة OpenAI للتفاعل مع ChatGPT
import os  # مكتبة os للوصول إلى متغيرات البيئة
import requests  # مكتبة requests لإرسال الإشعارات إلى واتساب
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# تعريف الحالات في المحادثة
CHAT, END_CHAT = range(2)

# متغيرات البيئة لمفاتيح API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # مفتاح API لـ OpenAI
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # رقم واتساب العيادة
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")  # API Key من CallMeBot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # مفتاح API لـ Telegram

# دالة الاتصال بـ GPT باستخدام تعليمات "رانية"
def ask_gpt_rania(user_input):
    openai.api_key = OPENAI_API_KEY  # تعيين مفتاح OpenAI

    response = openai.ChatCompletion.create(
        model="gpt-4",  # استخدم أقوى نموذج متاح لديك
        messages=[
            {"role": "system", "content": "مرحبًا! أنا رانية، مساعدتك الافتراضية في عيادة الدكتور خالد حسون الجراحية. كيف يمكنني مساعدتك اليوم؟"},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]

# دالة إرسال إشعار واتساب
def send_whatsapp_message(name, phone, chat_summary):
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}\n📌 ملخص المحادثة: {chat_summary}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# دالة بدء المحادثة
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا! أنا رانية، مساعدتك الافتراضية في عيادة الدكتور خالد حسون. كيف يمكنني مساعدتك اليوم؟")
    return CHAT

# استقبال الرسائل والتفاعل مع GPT
def chat(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text  # جلب رسالة المستخدم
    response = ask_gpt_rania(user_input)  # إرسالها إلى GPT والحصول على الرد
    update.message.reply_text(response)  # إرسال الرد للمستخدم

    # ✅ تخزين بيانات المحادثة في قائمة
    if "chat_summary" not in context.user_data:
        context.user_data["chat_summary"] = []
    context.user_data["chat_summary"].append(f"المستخدم: {user_input}\nرانية: {response}")
    
    return CHAT  # استمرار المحادثة

# إنهاء المحادثة وإرسال البيانات إلى واتساب
def end_chat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم إنهاء المحادثة، شكرًا لك!")
    
    name = context.user_data.get("name", "غير معروف")
    phone = context.user_data.get("phone", "غير معروف")
    chat_summary = "\n".join(context.user_data.get("chat_summary", []))
    
    # ✅ إرسال بيانات المحادثة إلى واتساب
    send_whatsapp_message(name, phone, chat_summary)
    
    return END_CHAT

# إعداد البوت وتشغيله
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHAT: [MessageHandler(Filters.text & ~Filters.command, chat)],
            END_CHAT: [CommandHandler("end", end_chat)]
        },
        fallbacks=[CommandHandler("end", end_chat)],
    )

    dp.add_handler(conv_handler)

    # 🔹 استخدام Webhook بدلاً من Polling
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get("PORT", 5000)),
                          url_path=TELEGRAM_BOT_TOKEN)

    updater.bot.setWebhook(f"https://{os.environ.get('RENDER_EXTERNAL_URL')}/{TELEGRAM_BOT_TOKEN}")

    updater.idle()

if __name__ == "__main__":
    main()
