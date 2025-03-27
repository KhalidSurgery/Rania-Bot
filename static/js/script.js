document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const bookBtn = document.getElementById('book-btn'); // زر الحجز الجديد

    // تحية أولية عند تحميل الصفحة
    displayMessage(`مرحباً! أنا رانية، مساعدتك في عيادة الدكتور خالد حسون الجراحية. كيف يمكنني مساعدتك اليوم؟`, 'bot');

    // إرسال الرسالة عند الضغط على زر الإرسال
    sendBtn.addEventListener('click', sendMessage);

    // إرسال الرسالة عند الضغط على Enter
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // معالج زر الحجز
    if (bookBtn) {
        bookBtn.addEventListener('click', function() {
            startBookingProcess();
        });
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // عرض رسالة المستخدم
        displayMessage(message, 'user');
        userInput.value = '';

        try {
            // إظهار مؤشر تحميل
            const loadingDiv = displayMessage('جاري معالجة طلبك...', 'bot');
            
            // إرسال السؤال للخادم
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            // إخفاء مؤشر التحميل
            chatBox.removeChild(loadingDiv);

            const data = await response.json();
            
            // معالجة الرد الخاص بالحجز
            if (data.bookingPrompt) {
                startBookingProcess();
            } else {
                // عرض رد المساعد مع معالجة الأسطر الجديدة
                displayMessage(data.answer.replace(/\n/g, '<br>'), 'bot');
            }

        } catch (error) {
            displayMessage('عذرًا، حدث خطأ في الاتصال بالمساعد. يرجى المحاولة لاحقًا.', 'bot', 'alert');
            console.error('Error:', error);
        }
    }

    function startBookingProcess() {
        // إخفاء زر الحجز إذا كان ظاهرًا
        if (bookBtn) bookBtn.style.display = 'none';
        
        // خطوات حجز الموعد
        displayMessage('لنبدأ بحجز موعدك. الرجاء إدخال المعلومات التالية:', 'bot');
        
        // إنشاء نموذج حجز
        const bookingForm = document.createElement('div');
        bookingForm.className = 'booking-form';
        bookingForm.innerHTML = `
            <div class="form-group">
                <label for="book-name">الاسم الكامل:</label>
                <input type="text" id="book-name" class="form-control" placeholder="الاسم الثلاثي">
            </div>
            <div class="form-group">
                <label for="book-phone">رقم الهاتف:</label>
                <input type="tel" id="book-phone" class="form-control" placeholder="07XXXXXXXX">
            </div>
            <div class="form-group">
                <label for="book-reason">سبب الزيارة:</label>
                <select id="book-reason" class="form-control">
                    <option value="استشارة طبية">استشارة طبية</option>
                    <option value="متابعة بعد عملية">متابعة بعد عملية</option>
                    <option value="فحص منظار">فحص منظار</option>
                    <option value="آخر">آخر</option>
                </select>
            </div>
            <div class="form-group">
                <label for="book-date">التاريخ المفضل:</label>
                <input type="date" id="book-date" class="form-control">
            </div>
            <div class="form-group">
                <label for="book-notes">ملاحظات إضافية (اختياري):</label>
                <textarea id="book-notes" class="form-control" rows="2"></textarea>
            </div>
            <button id="submit-booking" class="btn-submit">تأكيد الحجز</button>
        `;
        
        chatBox.appendChild(bookingForm);
        chatBox.scrollTop = chatBox.scrollHeight;

        // معالج إرسال الحجز
        document.getElementById('submit-booking').addEventListener('click', submitBooking);
    }

    async function submitBooking() {
        const name = document.getElementById('book-name').value.trim();
        const phone = document.getElementById('book-phone').value.trim();
        const reason = document.getElementById('book-reason').value;
        const date = document.getElementById('book-date').value;
        const notes = document.getElementById('book-notes').value.trim();

        // التحقق من البيانات المطلوبة
        if (!name || !phone || !date) {
            displayMessage('الرجاء إدخال جميع البيانات المطلوبة (الاسم، الهاتف، التاريخ)', 'bot', 'alert');
            return;
        }

        // التحقق من صحة رقم الهاتف
        if (!/^(07\d{8}|9647\d{8}|\+9647\d{8})$/.test(phone)) {
            displayMessage('رقم الهاتف غير صالح. يرجى استخدام الصيغة: 07XXXXXXXX', 'bot', 'alert');
            return;
        }

        try {
            // إرسال بيانات الحجز
            const response = await fetch('/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    phone: phone,
                    reason: reason,
                    date: date,
                    notes: notes
                })
            });

            const data = await response.json();

            if (data.success) {
                // إزالة نموذج الحجز
                const bookingForm = document.querySelector('.booking-form');
                if (bookingForm) chatBox.removeChild(bookingForm);
                
                // عرض تأكيد الحجز
                displayMessage(`
                    <strong>شكراً لك ${name}!</strong><br>
                    تم استلام حجزك بنجاح للتاريخ ${date}<br>
                    سبب الزيارة: ${reason}<br>
                    سنقوم بالتواصل معك على الرقم ${phone} لتأكيد الموعد.<br>
                    <span class="clinic-info">${data.message}</span>
                `, 'bot', 'booking');
                
                // إظهار زر الحجز مرة أخرى
                if (bookBtn) bookBtn.style.display = 'block';
            } else {
                displayMessage(`عذراً، حدث خطأ أثناء الحجز: ${data.error || 'يرجى المحاولة لاحقاً'}`, 'bot', 'alert');
            }

        } catch (error) {
            displayMessage('حدث خطأ في إرسال الحجز. يرجى المحاولة لاحقاً.', 'bot', 'alert');
            console.error('Booking Error:', error);
        }
    }

    function displayMessage(message, sender, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        // تحديد نوع الرسالة (عادي/حجز/تنبيه)
        if (type === 'booking') {
            messageDiv.classList.add('booking-message');
        } else if (type === 'alert') {
            messageDiv.classList.add('alert-message');
        }
        
        messageDiv.innerHTML = `<p>${message}</p>`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        
        return messageDiv;
    }
});
