// Configuration
let config = {
    baseUrl: localStorage.getItem('baseUrl') || 'http://localhost:8000',
    defaultChatbotId: localStorage.getItem('defaultChatbotId') || '1',
    defaultApiKey: localStorage.getItem('defaultApiKey') || ''
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeChat();
    initializeWidget();
    initializeAPI();
    initializeConfig();
    loadConfig();
});

// Tab Management
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked
            btn.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
}

// Chat Functionality
function initializeChat() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const chatbotId = document.getElementById('chatbotId');
    const apiKey = document.getElementById('apiKey');

    // Set defaults
    chatbotId.value = config.defaultChatbotId;
    apiKey.value = config.defaultApiKey;

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    clearChatBtn.addEventListener('click', () => {
        const messages = document.getElementById('chatMessages');
        messages.innerHTML = `
            <div class="message bot">
                <div class="message-content">
                    <p>Hello! I'm your chatbot assistant. How can I help you today?</p>
                </div>
            </div>
        `;
    });
}

let sessionId = null;

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatbotId = document.getElementById('chatbotId').value;
    const apiKey = document.getElementById('apiKey').value;
    const message = chatInput.value.trim();

    if (!message) return;
    if (!chatbotId || !apiKey) {
        alert('Please enter Chatbot ID and API Key');
        return;
    }

    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';

    // Show loading
    const loadingId = addMessage('Thinking...', 'bot', true);

    try {
        const response = await fetch(`${config.baseUrl}/api/public/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({
                chatbot_id: parseInt(chatbotId),
                message: message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        // Remove loading message
        document.getElementById(loadingId).remove();

        if (response.ok) {
            sessionId = data.session_id;
            addMessage(data.response, 'bot');
            if (data.sources && data.sources.length > 0) {
                const sourcesText = 'Sources: ' + data.sources.map(s => s.title || s.url).join(', ');
                addMessage(sourcesText, 'bot');
            }
        } else {
            addMessage(`Error: ${data.detail || 'Unknown error'}`, 'bot');
        }
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        addMessage(`Error: ${error.message}`, 'bot');
    }
}

function addMessage(text, type, isLoading = false) {
    const messages = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${isLoading ? '<span class="loading"></span> ' : ''}${text}</p>
        </div>
    `;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    return messageId;
}

// Widget Functionality
function initializeWidget() {
    const loadWidgetBtn = document.getElementById('loadWidgetBtn');
    const widgetChatbotId = document.getElementById('widgetChatbotId');
    const widgetApiKey = document.getElementById('widgetApiKey');
    const copyCodeBtn = document.getElementById('copyCodeBtn');

    // Set defaults
    widgetChatbotId.value = config.defaultChatbotId;
    widgetApiKey.value = config.defaultApiKey;

    loadWidgetBtn.addEventListener('click', loadWidget);
    copyCodeBtn.addEventListener('click', copyEmbedCode);
}

async function loadWidget() {
    const chatbotId = document.getElementById('widgetChatbotId').value;
    const apiKey = document.getElementById('widgetApiKey').value;
    const container = document.getElementById('widgetContainer');
    const embedCode = document.getElementById('embedCode');

    if (!chatbotId || !apiKey) {
        alert('Please enter Chatbot ID and API Key');
        return;
    }

    container.innerHTML = '<p>Loading widget...</p>';

    try {
        const response = await fetch(`${config.baseUrl}/api/public/widget/${chatbotId}?api_key=${apiKey}`);
        const html = await response.text();

        if (response.ok) {
            container.innerHTML = html;
            
            // Generate embed code
            const iframeCode = `<iframe 
  src="${config.baseUrl}/api/public/widget/${chatbotId}?api_key=${apiKey}"
  width="400"
  height="600"
  frameborder="0"
  style="border: none; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
</iframe>`;
            embedCode.value = iframeCode;
        } else {
            container.innerHTML = `<p style="color: red;">Error loading widget: ${response.statusText}</p>`;
        }
    } catch (error) {
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

function copyEmbedCode() {
    const embedCode = document.getElementById('embedCode');
    embedCode.select();
    document.execCommand('copy');
    alert('Embed code copied to clipboard!');
}

// API Testing
function initializeAPI() {
    document.getElementById('healthCheckBtn').addEventListener('click', testHealth);
    document.getElementById('testChatBtn').addEventListener('click', testChatAPI);
    document.getElementById('testWidgetBtn').addEventListener('click', testWidgetAPI);

    // Set defaults
    document.getElementById('apiChatbotId').value = config.defaultChatbotId;
    document.getElementById('apiKeyInput').value = config.defaultApiKey;
    document.getElementById('widgetApiChatbotId').value = config.defaultChatbotId;
    document.getElementById('widgetApiKeyInput').value = config.defaultApiKey;
}

async function testHealth() {
    const responseDiv = document.getElementById('healthResponse');
    responseDiv.textContent = 'Testing...';
    responseDiv.className = 'api-response';

    try {
        const response = await fetch(`${config.baseUrl}/health`);
        const data = await response.json();
        
        responseDiv.className = response.ok ? 'api-response success' : 'api-response error';
        responseDiv.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        responseDiv.className = 'api-response error';
        responseDiv.textContent = `Error: ${error.message}`;
    }
}

async function testChatAPI() {
    const chatbotId = document.getElementById('apiChatbotId').value;
    const apiKey = document.getElementById('apiKeyInput').value;
    const message = document.getElementById('apiMessage').value;
    const sessionId = document.getElementById('sessionId').value;
    const responseDiv = document.getElementById('chatResponse');

    if (!chatbotId || !apiKey || !message) {
        alert('Please fill in all required fields');
        return;
    }

    responseDiv.textContent = 'Testing...';
    responseDiv.className = 'api-response';

    try {
        const body = {
            chatbot_id: parseInt(chatbotId),
            message: message
        };
        if (sessionId) body.session_id = sessionId;

        const response = await fetch(`${config.baseUrl}/api/public/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        responseDiv.className = response.ok ? 'api-response success' : 'api-response error';
        responseDiv.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        responseDiv.className = 'api-response error';
        responseDiv.textContent = `Error: ${error.message}`;
    }
}

async function testWidgetAPI() {
    const chatbotId = document.getElementById('widgetApiChatbotId').value;
    const apiKey = document.getElementById('widgetApiKeyInput').value;
    const responseDiv = document.getElementById('widgetResponse');

    if (!chatbotId || !apiKey) {
        alert('Please enter Chatbot ID and API Key');
        return;
    }

    responseDiv.textContent = 'Testing...';
    responseDiv.className = 'api-response';

    try {
        const response = await fetch(`${config.baseUrl}/api/public/widget/${chatbotId}?api_key=${apiKey}`);
        const html = await response.text();

        responseDiv.className = response.ok ? 'api-response success' : 'api-response error';
        responseDiv.textContent = response.ok 
            ? `Widget HTML loaded successfully (${html.length} characters)\n\nPreview:\n${html.substring(0, 500)}...`
            : `Error: ${html}`;
    } catch (error) {
        responseDiv.className = 'api-response error';
        responseDiv.textContent = `Error: ${error.message}`;
    }
}

// Configuration
function initializeConfig() {
    document.getElementById('baseUrl').value = config.baseUrl;
    document.getElementById('defaultChatbotId').value = config.defaultChatbotId;
    document.getElementById('defaultApiKey').value = config.defaultApiKey;

    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);
}

function saveConfig() {
    config.baseUrl = document.getElementById('baseUrl').value;
    config.defaultChatbotId = document.getElementById('defaultChatbotId').value;
    config.defaultApiKey = document.getElementById('defaultApiKey').value;

    localStorage.setItem('baseUrl', config.baseUrl);
    localStorage.setItem('defaultChatbotId', config.defaultChatbotId);
    localStorage.setItem('defaultApiKey', config.defaultApiKey);

    // Update all input fields
    document.getElementById('chatbotId').value = config.defaultChatbotId;
    document.getElementById('apiKey').value = config.defaultApiKey;
    document.getElementById('widgetChatbotId').value = config.defaultChatbotId;
    document.getElementById('widgetApiKey').value = config.defaultApiKey;
    document.getElementById('apiChatbotId').value = config.defaultChatbotId;
    document.getElementById('apiKeyInput').value = config.defaultApiKey;
    document.getElementById('widgetApiChatbotId').value = config.defaultChatbotId;
    document.getElementById('widgetApiKeyInput').value = config.defaultApiKey;

    loadConfig();
    alert('Configuration saved!');
}

function loadConfig() {
    document.getElementById('configDisplay').textContent = JSON.stringify(config, null, 2);
}

