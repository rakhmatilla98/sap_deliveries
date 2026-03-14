// ai_chat.js - AI Assistant Chat Logic

document.addEventListener("DOMContentLoaded", () => {
    initAiChat();
});

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function initAiChat() {
    const chatInput = document.getElementById("aiChatInput");
    const sendBtn = document.getElementById("aiSendBtn");
    const recordBtn = document.getElementById("aiRecordBtn");

    if (!chatInput) return;

    // Toggle Send vs Record button
    chatInput.addEventListener("input", (e) => {
        if (e.target.value.trim().length > 0) {
            sendBtn.style.display = "flex";
            recordBtn.style.display = "none";
        } else {
            sendBtn.style.display = "none";
            recordBtn.style.display = "flex";
        }
    });

    // Enter to send
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendTextMessage();
        }
    });

    sendBtn.addEventListener("click", sendTextMessage);
    recordBtn.addEventListener("mousedown", startRecording);
    recordBtn.addEventListener("mouseup", stopRecording);
    recordBtn.addEventListener("touchstart", startRecording);
    recordBtn.addEventListener("touchend", stopRecording);
}

function formatAiPrice(price, currency = 'USD') {
    if (!price) return '';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}

function renderMessage(text, sender = "bot", items = []) {
    const container = document.getElementById("aiChatMessages");
    if (!container) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;

    let itemsHtml = "";
    if (items && items.length > 0) {
        itemsHtml = items.map(item => `
            <div class="chat-product-card">
                <div class="chat-product-header">
                    <div class="chat-product-name">${item.item_name}</div>
                    <div class="chat-product-price">${formatAiPrice(item.price, item.currency)}</div>
                </div>
                <div class="chat-product-actions product-card-actions" data-item-code="${item.item_code}">
                    <button class="add-btn" style="height: 30px; font-size: 12px;" onclick="event.stopPropagation(); window.addToCartById('${item.item_code}', 1, this)">
                        Add to Cart
                    </button>
                </div>
            </div>
        `).join("");
    }

    msgDiv.innerHTML = `
        <div class="message-content">
            <div>${text.replace(/\n/g, '<br>')}</div>
            ${itemsHtml ? `<div style="margin-top: 10px;">${itemsHtml}</div>` : ''}
        </div>
    `;

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;

    if (items && items.length > 0 && typeof window.syncProductButtons === 'function') {
        window.syncProductButtons();
    }
}

function showTyping() {
    const container = document.getElementById("aiChatMessages");
    const msgDiv = document.createElement("div");
    msgDiv.className = "chat-message bot typing-message";
    msgDiv.id = "typingIndicator";
    msgDiv.innerHTML = `
        <div class="message-content typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const indicator = document.getElementById("typingIndicator");
    if (indicator) {
        indicator.remove();
    }
}

async function sendTextMessage() {
    const input = document.getElementById("aiChatInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    document.getElementById("aiSendBtn").style.display = "none";
    document.getElementById("aiRecordBtn").style.display = "flex";

    renderMessage(text, "user");
    showTyping();

    const formData = new FormData();
    formData.append("text", text);
    
    await sendToBackend(formData);
}

async function startRecording(e) {
    if (e && e.cancelable) e.preventDefault();
    if (isRecording) return;
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Voice recording is not supported in your browser.");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            renderMessage("🎙️ Voice message sent", "user");
            showTyping();

            const formData = new FormData();
            formData.append("voice", audioBlob, "voice.webm");

            await sendToBackend(formData);
        };

        mediaRecorder.start();
        isRecording = true;
        document.getElementById("aiRecordBtn").classList.replace("btn-primary", "btn-danger");
    } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Microphone access denied.");
    }
}

function stopRecording(e) {
    if (e && e.cancelable) e.preventDefault();
    if (!isRecording || !mediaRecorder) return;
    
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
    isRecording = false;
    document.getElementById("aiRecordBtn").classList.replace("btn-danger", "btn-primary");
}

async function sendToBackend(formData) {
    try {
        const userId = window.telegramUserId || window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
        
        const res = await fetch("/api/ai-chat", {
            method: "POST",
            headers: {
                "X-Telegram-User-Id": userId ? userId.toString() : "123"
            },
            body: formData
        });

        hideTyping();

        if (!res.ok) {
            throw new Error(`API returned ${res.status}`);
        }

        const data = await res.json();
        
        renderMessage(data.replyText || "I couldn't process that.", "bot", data.items);
        
    } catch (err) {
        hideTyping();
        console.error("Chat error:", err);
        renderMessage("Sorry, I encountered an error communicating with the server.", "bot");
    }
}
