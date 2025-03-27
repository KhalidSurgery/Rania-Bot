from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
import os
import requests
from datetime import datetime
import re

# ===== التهيئة الأساسية =====
app = Flask(__name__, static_url_path='/static')

# اختر API Provider (OpenAI أو DeepSeek)
API_PROVIDER = os.getenv("API_PROVIDER", "deepseek")  # القيم الممكنة: openai / deepseek

if API_PROVIDER == "openai":
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elif API_PROVIDER == "deepseek":
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
else:
    raise ValueError("يجب تعيين API_PROVIDER إلى 'openai' أو 'deepseek'")

# ===== إعدادات العيادة =====
clinic_info = {
    "name": os.getenv("CLINIC_NAME", "عيادة الدكتور خالد حسون الجراحية"),
    "phone": os.getenv("EMERGENCY_PHONE", "0501234567"),
    "address": os.getenv("CLINIC_ADDRESS", "بغداد/ حي السلام (الطوبجي) / شارع السوق الشعبي"),
    "hours": os.getenv("WORKING_HOURS", "4 عصراً حتى 9 مساءً (السبت-الخميس)"),
    "fees": os.getenv("CONSULTATION_FEE", "20,000 دينار عراقي"),
    "map_url": "https://maps.app.goo.gl/gEziJm4zfmdxirUXA",
    "website": "www.kscssc.com"
}

# ===== التعليمات الطبية المحسنة =====
MEDICAL_GUIDE = f"""
▄▀▄▀▄【 رانية - المساعدة الذكية لـ {clinic_info['name']} 】▄▀▄▀▄

⚕️【 المهمة 】:
1. الرد على استفسارات المرضى حول المواعيد، الرسوم، الخدمات
2. جمع بيانات الحجز بدقة (الاسم، الهاتف، السبب، التاريخ)
3. توجيه الاستفسارات الطبية حسب تخصص العيادة
4. توثيق جميع المحادثات وإرسالها للتوثيق

📌【 تخصصات العيادة 】:
- جراحة الجهاز الهضمي والقولون
- جراحات البطن الطارئة
- جراحة الغدد والأنسجة الرخوة
- جراحة الأورام والثدي
- الجراحة المنظارية
- فحص المنظار للجهاز الهضمي

📞【 معلومات العيادة 】:
- هاتف: {clinic_info['phone']}
- العنوان: {clinic_info['address']}
- أوقات العمل: {clinic_info['hours']}
- رسوم الكشف: {clinic_info['fees']}
- الخريطة: {clinic_info['map_url']}

📋【 نمط الرد 】:
ابدأ التحية بـ: "مرحباً! أنا رانية، مساعدتك في {clinic_info['name']}. كيف أستطيع مساعدتك؟"

🔹 عند الحجز:
1. اطلب الاسم الكامل
2. اطلب رقم الهاتف (يتحقق من صحته)
3. اسأل عن سبب الزيارة
4. اسأل عن التاريخ المفضل
5. قدم تأكيداً للحجز

🔹 عند الاستفسار:
- للساعات: "العيادة تعمل من {clinic_info['hours']}"
- للرسوم: "رسوم الكشف {clinic_info['fees']}"
- للموقع: "العنوان: {clinic_info['address']} - الخريطة: {clinic_info['map_url']}"
- للتخصص: "الدكتور خالد حسون استشاري جراحة عامة متخصص في [ذكر التخصص المناسب]"

⚠️【 تنبيهات 】:
- لا تقم بالتشخيص أو وصف العلاج
- للحالات الطارئة: "الرجاء التوجه لأقرب مستشفى"
- أنهِ المحادثة بـ: "شكراً لاختيارك عيادتنا، نحن هنا لخدمتك"
"""

# ===== دوال المساعدة =====
def validate_phone(phone):
    """تحقق من صحة رقم الهاتف العراقي"""
    phone = str(phone).strip()
    # الصيغ المقبولة: 07XXXXXXXX أو 9647XXXXXXXX أو +9647XXXXXXXX
    if re.fullmatch(r'^(07\d{9}|9647\d{9}|\+9647\d{9})$', phone):
        return True
    return False

def format_booking_data(name, phone, reason, date, notes=""):
    """تنسيق بيانات الحجز لإرسالها"""
    return f"""
- **اسم المريض**: {name}
- **رقم الهاتف**: {phone}
- **سبب الزيارة**: {reason}
- **التاريخ المطلوب**: {date}
- **تفاصيل إضافية**: {notes if notes else "لا يوجد"}
"""

def send_whatsapp(msg):
    """إرسال رسالة واتساب"""
    try:
        if not (os.getenv("WHATSAPP_NUMBER") and os.getenv("CALLMEBOT_API_KEY")):
            return False
            
        url = f"https://api.callmebot.com/whatsapp.php?phone={os.getenv('WHATSAPP_NUMBER')}&text={msg}&apikey={os.getenv('CALLMEBOT_API_KEY')}"
        requests.get(url, timeout=10)
        return True
    except Exception as e:
        print(f"[WhatsApp Error] {str(e)}")
        return False

def get_ai_response(messages):
    """دالة موحدة للتعامل مع مختلف مزودي API"""
    try:
        if API_PROVIDER == "openai":
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        elif API_PROVIDER == "deepseek":
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.3
            }
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
    except Exception as e:
        print(f"[AI API Error] {str(e)}")
        return "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة لاحقاً."

# ===== الروتات الأساسية =====
@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.json.get('question', '').strip()
        if not question:
            return jsonify({"error": "الرجاء إدخال سؤال"}), 400

        # معالجة الأسئلة الشائعة مباشرة دون اللجوء للذكاء الاصطناعي
        if any(q in question.lower() for q in ["مواعيد", "اوقات", "وقت"]):
            return jsonify({"answer": f"أوقات العمل: {clinic_info['hours']}"})
            
        elif any(q in question.lower() for q in ["رسوم", "سعر", "تكلفة"]):
            return jsonify({"answer": f"رسوم الكشف: {clinic_info['fees']}"})
            
        elif any(q in question.lower() for q in ["عنوان", "موقع", "خريطة"]):
            return jsonify({"answer": f"العنوان: {clinic_info['address']}\nالخريطة: {clinic_info['map_url']}"})
            
        elif any(q in question.lower() for q in ["تخصص", "اختصاص"]):
            specialties = [
                "جراحة الجهاز الهضمي والقولون",
                "جراحات البطن الطارئة",
                "جراحة الغدد والأنسجة الرخوة",
                "جراحة الأورام والثدي",
                "الجراحة المنظارية",
                "فحص المنظار للجهاز الهضمي"
            ]
            return jsonify({"answer": f"تخصصات العيادة:\n- " + "\n- ".join(specialties)})

        messages = [
            {"role": "system", "content": MEDICAL_GUIDE},
            {"role": "user", "content": question}
        ]
        
        answer = get_ai_response(messages)
        return jsonify({"answer": answer})
        
    except Exception as e:
        print(f"[Ask Endpoint Error] {str(e)}")
        return jsonify({
            "error": "عذراً، حدث خطأ في معالجة سؤالك",
            "details": str(e)
        }), 500

@app.route('/book', methods=['POST'])
def book():
    try:
        data = request.json
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        reason = data.get('reason', '').strip()
        date = data.get('date', '').strip()
        notes = data.get('notes', '').strip()
        
        # التحقق من البيانات المطلوبة
        if not all([name, phone, reason, date]):
            return jsonify({"error": "جميع الحقول مطلوبة ما عدا التفاصيل الإضافية"}), 400
            
        # التحقق من صحة رقم الهاتف
        if not validate_phone(phone):
            return jsonify({"error": "رقم الهاتف غير صالح. يرجى استخدام الصيغة: 07XXXXXXXX"}), 400
            
        # تنسيق الرسالة
        booking_msg = format_booking_data(name, phone, reason, date, notes)
        full_msg = f"حجز موعد جديد في {clinic_info['name']}\n{booking_msg}"
        
        # إرسال الواتساب
        if not send_whatsapp(full_msg):
            print(f"[Booking Failed] WhatsApp not sent: {full_msg}")
            
        return jsonify({
            "success": True,
            "message": "تم استلام الحجز بنجاح، سنتواصل معك خلال 24 ساعة لتأكيد الموعد"
        })
        
    except Exception as e:
        print(f"[Book Endpoint Error] {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء الحجز"}), 500

# ===== تشغيل التطبيق =====
if __name__ == '__main__':
    from waitress import serve
    print(f"✅ تم التشغيل بنجاح باستخدام {API_PROVIDER.upper()} API")
    serve(app, host="0.0.0.0", port=5000)
