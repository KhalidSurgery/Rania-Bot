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
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_BOT_TOKEN}"

# دالة الاتصال بـ GPT مع تعليمات "رانية"
def ask_gpt_rania(user_input):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": """مرحبًا! أنا رانية، مساعدتك الافتراضية في عيادة الدكتور خالد حسون الجراحية.
            
مهمتي:
1. الرد على استفسارات المرضى حول مواعيد العيادة، الرسوم، والخدمات.
2. جمع البيانات الأساسية (الاسم، الهاتف، سبب الزيارة، التاريخ) وإرسالها للتوثيق.
3. معالجة طلبات الحجز والاستفسارات الطبية العامة.
4. التأكد من صحة البيانات قبل إرسالها.
5. توجيه المريض لمزيد من المعلومات عبر الروابط الرسمية.

📌 **خطوات التعامل مع المرضى:**
- **الترحيب بالمريض:** "مرحبًا! كيف يمكنني مساعدتك اليوم؟"
- **جمع البيانات:** "يرجى إدخال اسمك، رقم هاتفك، وسبب زيارتك."
- **تأكيد البيانات:** إرسالها إلى واتساب للتوثيق.
- **الرد على الاستفسارات العامة:** العنوان، الأوقات، الأسعار، والخدمات.
- **معالجة الأخطاء:** التحقق من صحة رقم الهاتف وإعادة الطلب عند الضرورة.

📌 **معلومات العيادة:**
- **العنوان:** بغداد/ حي السلام (الطوبجي) / شارع السوق الشعبي/ مجاور ماركت ابو عماد / مقابل مكتب القريشي ومكتب البريد.
- **أوقات العمل:** 4 عصرًا - 9 مساءً (السبت - الخميس).
- **تكلفة الكشف:** 20,000 دينار عراقي.
- **الخدمات:** استشارات طبية، عمليات جراحية، متابعة ما بعد العمليات.

📌 **روابط العيادة:**
- الموقع الرسمي: [www.kscssc.com](http://www.kscssc.com)
- مكتبة الكتب الطبية: [maktaba.kscssc.com](http://maktaba.kscssc.com)
- شركة ميديرونزا: [www.medironza.com](http://www.medironza.com)
- نشر الكتب: [publishing.medironza.com](http://publishing.medironza.com)

📌 **تنبيهات:**
- إذا كان الرقم خاطئًا، أطلب من المراجع تصحيحه.
- لا تُشخّص الحالات الطبية، فقط قم بتوجيه المريض لحجز موعد مع الطبيب.
- تأكد من تنسيق البيانات عند إرسالها إلى واتساب بالشكل التالي:
  - **اسم المراجع:** [الاسم]
  - **رقم الهاتف:** [الهاتف]
  - **سبب الزيارة:** [الحجز، استفسار، شكوى]
  - **التاريخ المطلوب:** [التاريخ]
  - **ملخص المحادثة:** [تفاصيل المحادثة]
"""},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]

# إرسال إشعار واتساب
def send_whatsapp_message(name, phone, chat_summary):
    message = f"📢 مريض جديد:\n👤 الاسم: {name}\n📞 الهاتف: {phone}\n📌 ملخص المحادثة:\n{chat_summary}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={message}&apikey={CALLMEBOT_API_KEY}"
    requests.get(url)

# بدء المحادثة
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("مرحبًا! أنا رانية، مساعدتك الافتراضية. كيف يمكنني مساعدتك اليوم؟")
    return CHAT

# استقبال الرسائل والتفاعل مع GPT
def chat(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    response = ask_gpt_rania(user_input)
    update.message.reply_text(response)

    # تخزين بيانات المحادثة
    if "chat_summary" not in context.user_data:
        context.user_data["chat_summary"] = []
    context.user_data["chat_summary"].append(f"المستخدم: {user_input}\nرانية: {response}")

    return CHAT

# إنهاء المحادثة وإرسال البيانات إلى واتساب
def end_chat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("تم إنهاء المحادثة، شكرًا لك!")
    
    name = context.user_data.get("name", "غير معروف")
    phone = context.user_data.get("phone", "غير معروف")
    chat_summary = "\n".join(context.user_data.get("chat_summary", []))

    # إرسال البيانات إلى واتساب
    send_whatsapp_message(name, phone, chat_summary)

    return END_CHAT

# إعداد البوت باستخدام Webhook
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CHAT: [MessageHandler(Filters.text & ~Filters.command, chat)], END_CHAT: [CommandHandler("end", end_chat)]},
        fallbacks=[CommandHandler("end", end_chat)],
    )

    dp.add_handler(conv_handler)

    # تشغيل Webhook بدلاً من Polling
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),  # استخدم المنفذ الصحيح
        url_path=TELEGRAM_BOT_TOKEN
    )
    updater.bot.setWebhook(WEBHOOK_URL)

    updater.idle()

if __name__ == "__main__":
    main()
