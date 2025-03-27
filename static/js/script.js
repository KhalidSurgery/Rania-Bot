document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // إرسال الرسالة عند الضغط على زر الإرسال
    sendBtn.addEventListener('click', sendMessage);

    // إرسال الرسالة عند الضغط على Enter
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // عرض رسالة المستخدم
        displayMessage(message, 'user');
        userInput.value = '';

        try {
            // إرسال السؤال للخادم
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();
            
            // عرض رد المساعد
            displayMessage(data.answer, 'bot');

        } catch (error) {
            displayMessage('عذرًا، حدث خطأ في الاتصال بالمساعد', 'bot');
            console.error('Error:', error);
        }
    }

    function displayMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.innerHTML = `<p>${message}</p>`;
        
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
