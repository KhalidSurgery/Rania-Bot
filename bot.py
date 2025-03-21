from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import requests
import os

# مراحل المحادثة
ASK_NAME, ASK_PHONE, CHAT = range(3)  # ✅ تم التأكد من تعريف CHAT بشكل صحيح

# إعدادات إشعار واتساب (باستخدام CallMeBot)
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # رقم واتساب العيادة
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")  # API Key من CallMeBot

# دالة إرسال إشعار واتساب
def send_whatsapp_message(name, phone):
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء البوت
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("مرحبًا! أنا رانية، المساعد الذكي لعيادة د. خالد حسون. من فضلك أدخل اسمك للمتابعة.")
    return ASK_NAME

# طلب الاسم
async def ask_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("شكرًا! الآن أدخل رقم هاتفك.")
    return ASK_PHONE

# طلب رقم الهاتف
async def ask_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    if not phone.isdigit():  # ✅ التأكد من أن المدخل يحتوي فقط على أرقام
        await update.message.reply_text("الرجاء إدخال رقم هاتف صحيح.")
        return ASK_PHONE

    context.user_data['phone'] = phone
    name = context.user_data['name']

    # إرسال إشعار إلى واتساب
    send_whatsapp_message(name, phone)

    await update.message.reply_text(f"شكرًا {name}! يمكنك الآن طرح استفساراتك.")
    return CHAT  # ✅ الآن CHAT معرف بشكل صحيح

# استقبال الرسائل من المستخدم
async def chat(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("تم استلام الرسالة، شكرًا لك!")
    return ConversationHandler.END

# دالة إلغاء المحادثة
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("تم إلغاء المحادثة. يمكنك البدء من جديد بإرسال /start")
    return ConversationHandler.END

# إعداد البوت
def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],  # ✅ تم التأكد من أن CHAT معرف
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
