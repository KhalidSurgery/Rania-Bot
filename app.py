from flask import Flask, request, jsonify, render_template
import openai
import os

app = Flask(__name__)

# تعليمات المساعد الطبي
MEDICAL_GUIDE = """
أنت مساعد طبي لعيادة الدكتور/خالد الجراحية.
المهام:
- الرد على استفسارات ما قبل الجراحة
- شرح الإجراءات الروتينية
- توجيه الحالات الطارئة للعيادة
الممنوعات:
- لا تقم بتشخيص
- لا تصف أدوية
"""

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": MEDICAL_GUIDE},
            {"role": "user", "content": question}
        ]
    )
    
    return jsonify({
        "answer": response.choices[0].message.content
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
