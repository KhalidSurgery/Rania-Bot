from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import requests
import os

# مراحل المحادثة
ASK_NAME, ASK_PHONE, CHAT = range(3)

# إعدادات إشعار واتساب (باستخدام CallMeBot)
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # رقم واتساب العيادة
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")  # API Key من CallMeBot

# دالة إرسال إشعار واتساب
def send_whatsapp_message(name, phone):
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء البوت
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا! أنا رانية، المساعد الذكي لعيادة د. خالد حسون. من فضلك أدخل اسمك للمتابعة.")
    return ASK_NAME

# طلب الاسم
def ask_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("شكرًا! الآن أدخل رقم هاتفك.")
    return ASK_PHONE

# طلب رقم الهاتف
def ask_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['phone'] = update.message.text
    name = context.user_data['name']
    phone = context.user_data['phone']

    # إرسال إشعار إلى واتساب
    send_whatsapp_message(name, phone)

    update.message.reply_text(f"شكرًا {name}! يمكنك الآن طرح استفساراتك.")
    return CHAT
def chat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم استلام الرسالة، شكرًا لك!")
    return ConversationHandler.END

# إعداد البوت
def main():
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_name)],
            ASK_PHONE: [MessageHandler(Filters.text & ~Filters.command, ask_phone)],
            CHAT: [MessageHandler(Filters.text & ~Filters.command, chat)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
