import asyncio
import os
import openai
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)
from telegram.error import Conflict, NetworkError

# تعريف حالات المحادثة
CHAT, END_CHAT = range(2)

# جلب مفاتيح API من متغيرات البيئة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# التحقق من وجود المفاتيح
if not OPENAI_API_KEY:
    raise ValueError("يجب تعيين OPENAI_API_KEY في متغيرات البيئة")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("يجب تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

# تهيئة OpenAI
openai.api_key = OPENAI_API_KEY

def ask_gpt_rania(user_input: str) -> str:
    """استدعاء نموذج GPT-4 للحصول على إجابة"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "مرحبًا! أنا رانية، مساعدتك الافتراضية في عيادة الدكتور خالد حسون."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

def send_whatsapp_notification(name: str, phone: str, summary: str) -> None:
    """إرسال إشعار عبر واتساب"""
    if not WHATSAPP_NUMBER or not CALLMEBOT_API_KEY:
        return
        
    message = (
        f"📢 مريض جديد بدأ المحادثة:\n"
        f"👤 الاسم: {name}\n"
        f"📞 الهاتف: {phone}\n"
        f"📌 ملخص المحادثة: {summary}"
    )
    url = (
        f"https://api.callmebot.com/whatsapp.php?"
        f"phone={WHATSAPP_NUMBER}&"
        f"text={message}&"
        f"apikey={CALLMEBOT_API_KEY}"
    )
    requests.get(url, timeout=10)

async def start(update: Update, context: CallbackContext) -> int:
    """بدء المحادثة مع المستخدم"""
    await update.message.reply_text(
        "مرحبًا! أنا رانية، المساعدة الافتراضية في عيادة الدكتور خالد حسون.\n"
        "كيف يمكنني مساعدتك اليوم؟"
    )
    return CHAT

async def chat(update: Update, context: CallbackContext) -> int:
    """معالجة رسائل المستخدم"""
    user_input = update.message.text
    try:
        response = ask_gpt_rania(user_input)
        await update.message.reply_text(response)
        
        # إرسال إشعار واتساب (اختياري)
        if update.message.from_user:
            send_whatsapp_notification(
                name=update.message.from_user.full_name,
                phone="غير معروف",
                summary=user_input[:100]  # إرسال أول 100 حرف من المحادثة
            )
            
    except Exception as e:
        print(f"خطأ في معالجة الرسالة: {e}")
        await update.message.reply_text("عذرًا، حدث خطأ أثناء معالجة طلبك.")
    
    return CHAT

async def end_chat(update: Update, context: CallbackContext) -> int:
    """إنهاء المحادثة"""
    await update.message.reply_text(
        "شكرًا لك على تواصلك معنا. "
        "لا تتردد في البدء بمحادثة جديدة إذا كان لديك أي استفسارات أخرى."
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: CallbackContext) -> None:
    """معالج الأخطاء العام"""
    print(f"حدث خطأ: {context.error}")
    if update and update.message:
        await update.message.reply_text("عذرًا، حدث خطأ غير متوقع.")

async def run_bot() -> None:
    """تشغيل البوت الرئيسي"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # إعداد محادثة البوت
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[CommandHandler('end', end_chat)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    try:
        # تنظيف التحديثات القديمة قبل البدء
        await application.bot.delete_webhook(drop_pending_updates=True)
        
        print("✅ البوت يعمل الآن...")
        await application.run_polling(
            poll_interval=1.0,
            timeout=10,
            drop_pending_updates=True
        )
        
    except Conflict:
        print("⚠️ خطأ: تم اكتشاف نسخة أخرى من البوت تعمل بالفعل!")
    except NetworkError as e:
        print(f"⚠️ خطأ شبكة: {e}")
    except Exception as e:
        print(f"⚠️ خطأ غير متوقع: {e}")
    finally:
        if application.running:
            await application.stop()
            print("⏹️ تم إيقاف البوت")

async def main() -> None:
    """الدالة الرئيسية مع إعادة تشغيل تلقائي"""
    while True:
        try:
            await run_bot()
        except Exception as e:
            print(f"🔄 إعادة التشغيل بسبب خطأ: {e}")
            await asyncio.sleep(5)  # انتظار 5 ثوان قبل إعادة المحاولة

if __name__ == "__main__":
    try:
        print("🚀 بدء تشغيل بوت التليجرام...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"💥 خطأ حرج: {e}")
