from flask import Flask, render_template, request, jsonify, send_from_directory
import openai
import os
import requests
from datetime import datetime

# تهيئة التطبيق
app = Flask(__name__, static_url_path='/static')

# تعليمات المساعد الطبي
MEDICAL_GUIDE = """
أنت مساعد طبي متخصص في عيادة الدكتور خالد حسون الجراحية.
المهام:
1. الرد على استفسارات العمليات الجراحية
2. شرح التحضيرات اللازمة قبل الجراحة
3. تقديم التعليمات ما بعد العملية
4. توجيه الحالات الطارئة للعيادة مباشرة

الممنوعات:
- لا تقم بتشخيص أي حالة
- لا تصف أي أدوية
- لا تعطي وصفات طبية

المعلومات الأساسية:
- العيادة: الرياض، حي الملك فهد
- هاتف الطوارئ: 0501234567
- أوقات العمل: من الأحد إلى الخميس (8 ص - 4 م)
"""

# الأسئلة الشائعة
FAQ = {
    "التكلفة": "تختلف التكلفة حسب نوع الجراحة، يرجى التواصل مع الإدارة للحصول على تفاصيل دقيقة",
    "التحضير": "الصيام 8 ساعات قبل الجراحة، وإحضار جميع التقارير الطبية السابقة",
    "المدة": "معظم الجراحات تستغرق من 1 إلى 3 ساعات حسب الحالة"
}

# دالة إرسال إشعار الواتساب
def send_whatsapp_notification(message):
    try:
        whatsapp_number = os.getenv("WHATSAPP_NUMBER")
        api_key = os.getenv("CALLMEBOT_API_KEY")
        
        if not whatsapp_number or not api_key:
            return False
            
        url = f"https://api.callmebot.com/whatsapp.php?phone={whatsapp_number}&text={message}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('chat.html')

# معالجة الأسئلة
@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "الرجاء إدخال سؤال"}), 400
        
        # التحقق من الأسئلة الشائعة أولاً
        if user_question in FAQ:
            return jsonify({"answer": FAQ[user_question]})
            
        # استخدام الذكاء الاصطناعي للإجابة
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": MEDICAL_GUIDE},
                {"role": "user", "content": user_question}
            ],
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        return jsonify({"answer": answer})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء معالجة السؤال"}), 500

# حجز المواعيد
@app.route('/book', methods=['POST'])
def book_appointment():
    try:
        data = request.json
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        date = data.get('date', '').strip()
        
        if not all([name, phone, date]):
            return jsonify({"error": "جميع الحقول مطلوبة"}), 400
            
        # إرسال إشعار الواتساب
        notification_msg = f"حجز موعد جديد:\nالاسم: {name}\nالهاتف: {phone}\nالتاريخ: {date}"
        send_whatsapp_notification(notification_msg)
        
        return jsonify({
            "success": True,
            "message": "تم استلام طلب الحجز، سنتواصل معك خلال 24 ساعة للتأكيد"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء حجز الموعد"}), 500

# خدمة الملفات الثابتة
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

if __name__ == '__main__':
    # تحميل متغيرات البيئة
    from dotenv import load_dotenv
    load_dotenv()
    
    # التحقق من المفاتيح
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("يجب تعيين OPENAI_API_KEY في ملف .env")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
