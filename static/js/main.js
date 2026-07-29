/* ==========================================================================
   AI Medical Report Summarization System - Main Interactive JS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    // ----------------------------------------------------
    // 1. Drag and Drop File Upload Logic
    // ----------------------------------------------------
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('report_file');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileInfoBadge = document.getElementById('file-info');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                updateFileDisplay(fileInput.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                updateFileDisplay(fileInput.files[0]);
            }
        });

        function updateFileDisplay(file) {
            if (file) {
                fileNameDisplay.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
                fileInfoBadge.classList.remove('hidden');
            }
        }
    }

    // ----------------------------------------------------
    // 2. Upload Form Submission Loading Animation
    // ----------------------------------------------------
    const uploadForm = document.getElementById('upload-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingStepText = document.getElementById('loading-step-text');

    if (uploadForm && loadingOverlay) {
        uploadForm.addEventListener('submit', function () {
            loadingOverlay.classList.remove('hidden');
            
            const steps = [
                "Step 1/3: Extracting medical text from PDF...",
                "Step 2/3: Chunking & Indexing into ChromaDB Vectorstore...",
                "Step 3/3: Executing Mistral-7B Clinical Prompt Engineering...",
                "Finalizing PDF summary report output..."
            ];

            let stepIdx = 0;
            const interval = setInterval(() => {
                stepIdx++;
                if (stepIdx < steps.length) {
                    loadingStepText.textContent = steps[stepIdx];
                } else {
                    clearInterval(interval);
                }
            }, 1200);
        });
    }

    // ----------------------------------------------------
    // 3. Interactive RAG Chatbot Assistant
    // ----------------------------------------------------
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const question = chatInput.value.trim();
            const reportId = chatForm.dataset.reportId;
            if (!question) return;

            // Append User Message
            appendChatMessage('user', question);
            chatInput.value = '';

            // Append Loading Indicator
            const loadingMsgId = appendChatMessage('assistant', '<i>Thinking & searching ChromaDB context...</i>');

            // Send API Request
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    report_id: reportId,
                    question: question
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.answer) {
                    updateChatMessage(loadingMsgId, formatMarkdownText(data.answer));
                } else {
                    updateChatMessage(loadingMsgId, 'Sorry, an error occurred while searching context.');
                }
            })
            .catch(err => {
                console.error(err);
                updateChatMessage(loadingMsgId, 'Failed to connect to RAG server.');
            });
        });
    }
});

// Helper: Quick Prompt Trigger
function sendQuickPrompt(promptText) {
    const chatInput = document.getElementById('chat-input');
    const chatForm = document.getElementById('chat-form');
    if (chatInput && chatForm) {
        chatInput.value = promptText;
        chatForm.dispatchEvent(new Event('submit'));
    }
}

// Helper: Append Chat Message to UI
function appendChatMessage(sender, text) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const msgId = 'msg-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.className = `chat-message ${sender === 'user' ? 'user-msg' : 'assistant-msg'}`;

    const avatarIcon = sender === 'user' ? 'fa-user' : 'fa-user-doctor';
    
    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid ${avatarIcon}"></i></div>
        <div class="msg-content">${text}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgId;
}

// Helper: Update Chat Message Content
function updateChatMessage(msgId, newText) {
    const msgDiv = document.getElementById(msgId);
    if (msgDiv) {
        const contentDiv = msgDiv.querySelector('.msg-content');
        if (contentDiv) {
            contentDiv.innerHTML = newText;
        }
    }
}

// Simple Markdown Formatter
function formatMarkdownText(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>');
}
