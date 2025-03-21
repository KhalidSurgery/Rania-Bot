from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import requests
import os

# تعريف مراحل المحادثة
ASK_NAME, ASK_PHONE, CHAT = range(3)

# إعدادات إشعار واتساب (باستخدام CallMeBot)
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # رقم واتساب العيادة
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")  # API Key من CallMeBot

# دالة إرسال إشعار واتساب
def send_whatsapp_message(name, phone):
    message = f"📢 مريض جديد بدأ المحادثة:\n👤 الاسم: {name}\n📞 الهاتف: {phone}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء المحادثة
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا! أنا رانية، المساعد الذكي لعيادة د. خالد حسون. من فضلك أدخل اسمك للمتابعة.")
    return ASK_NAME

# طلب الاسم
def ask_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("شكرًا! الآن أدخل رقم هاتفك.")
    return ASK_PHONE

import re  # مكتبة للتحقق من الأرقام

def is_valid_phone_number(phone):
    """ التحقق من صحة رقم الهاتف المدخل """
    phone = re.sub(r'\D', '', phone)  # إزالة أي أحرف غير رقمية
    if phone.startswith("964") and len(phone) == 12:
        return phone  # الرقم صحيح
    elif phone.startswith("0") and len(phone) == 11:
        return "964" + phone[1:]  # تحويل الرقم إلى الصيغة الدولية
    else:
        return None  # رقم غير صالح

# طلب رقم الهاتف
def ask_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text.strip()
    valid_phone = is_valid_phone_number(phone)  # تحقق من صحة الرقم

    if valid_phone:
        context.user_data['phone'] = valid_phone
        name = context.user_data['name']

        # ✅ طباعة البيانات للتأكد قبل الإرسال إلى واتساب
        print(f"📞 إرسال إلى واتساب: {valid_phone}, 👤 اسم المريض: {name}")

        # ✅ إرسال البيانات إلى واتساب
        send_whatsapp_message(name, valid_phone)

        update.message.reply_text(f"شكرًا {name}! يمكنك الآن طرح استفساراتك.")
        return CHAT  # ✅ هذا داخل `if`

    else:
        update.message.reply_text("⚠️ رقم الهاتف غير صحيح. يرجى إدخال رقم عراقي صحيح بصيغة 07XXXXXXXXX أو 964XXXXXXXXX.")
        return ASK_PHONE  # ✅ هذا داخل `else`


# التعامل مع المحادثة العامة بعد إدخال البيانات
def chat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم استلام الرسالة، شكرًا لك!")
    return ConversationHandler.END

# إلغاء المحادثة
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم إلغاء المحادثة. إذا كنت بحاجة إلى المساعدة، استخدم /start للبدء مجددًا.")
    return ConversationHandler.END

# إعداد البوت وتشغيله
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
