from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI  # تغيير طريقة الاستيراد
import os
import requests
from datetime import datetime

# ===== التهيئة الأساسية =====
app = Flask(__name__, static_url_path='/static')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # تهيئة العميل الجديد

# ===== إعدادات العيادة =====
clinic_info = {
    "name": os.getenv("CLINIC_NAME", "عيادة الدكتور خالد حسون الجراحية"),
    "phone": os.getenv("EMERGENCY_PHONE", "0501234567"),
    "address": os.getenv("CLINIC_ADDRESS", "الرياض، حي الملك فهد، شارع التحلية"),
    "hours": os.getenv("WORKING_HOURS", "الأحد-الخميس 8 صباحاً - 4 مساءً")
}

MEDICAL_GUIDE = f"""
أنت مساعد طبي في {clinic_info['name']}.
المعلومات الأساسية:
- 📞 هاتف الطوارئ: {clinic_info['phone']}
- 🏥 العنوان: {clinic_info['address']}
- ⏰ أوقات العمل: {clinic_info['hours']}

القواعد:
1. ❌ لا تقم بتشخيص الأمراض
2. 💊 لا تصف أدوية
3. 🚨 للحالات الطارئة: اتصل بالرقم أعلاه مباشرة
"""

# ===== دوال المساعدة =====
def send_whatsapp(msg):
    try:
        if not (os.getenv("WHATSAPP_NUMBER") and os.getenv("CALLMEBOT_API_KEY")):
            return False
            
        url = f"https://api.callmebot.com/whatsapp.php?phone={os.getenv('WHATSAPP_NUMBER')}&text={msg}&apikey={os.getenv('CALLMEBOT_API_KEY')}"
        requests.get(url, timeout=5)
        return True
    except:
        return False

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

        response = client.chat.completions.create(  # التعديل هنا
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": MEDICAL_GUIDE},
                {"role": "user", "content": question}
            ],
            temperature=0.3
        )
        
        return jsonify({"answer": response.choices[0].message.content})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "حدث خطأ في معالجة سؤالك"}), 500

@app.route('/book', methods=['POST'])
def book():
    try:
        data = request.json
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        date = data.get('date', '').strip()
        
        if not all([name, phone, date]):
            return jsonify({"error": "جميع الحقول مطلوبة"}), 400
            
        msg = f"""حجز موعد جديد:
الاسم: {name}
الهاتف: {phone}
التاريخ: {date}
العيادة: {clinic_info['name']}"""
        
        send_whatsapp(msg)
        
        return jsonify({
            "success": True,
            "message": "تم استلام الحجز بنجاح، سنتواصل معك خلال 24 ساعة"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء الحجز"}), 500

# ===== تشغيل التطبيق =====
def create_app(environ=None, start_response=None):
    if environ and start_response:
        return app(environ, start_response)
    return app

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
