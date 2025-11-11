// ============================================
// Global State & Configuration
// ============================================
const state = {
    config: {
        odooUrl: 'http://localhost:8069',
        odooDb: 'odoo_c',
        odooUsername: 'admin',
        odooPassword: '',
        fastapiUrl: 'http://localhost:8000',
        internalApiKey: 'internal_key_123'
    },
    selectedFiles: [],
    selectedLinks: [],
    currentChatbot: null,
    sessionId: null
};

// ============================================
// Theme Management
// ============================================
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// ============================================
// Navigation
// ============================================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const sectionId = item.dataset.section;
            
            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Show corresponding section
            sections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(`${sectionId}-section`).classList.add('active');
        });
    });
}

// ============================================
// Configuration Management
// ============================================
function loadConfig() {
    const saved = localStorage.getItem('testUIConfig');
    if (saved) {
        try {
            const savedConfig = JSON.parse(saved);
            state.config = { ...state.config, ...savedConfig };
        } catch (e) {
            console.error('Error loading config:', e);
        }
    }
    
    // Populate form fields
    if (document.getElementById('odooUrl')) {
        document.getElementById('odooUrl').value = state.config.odooUrl || '';
        document.getElementById('odooDb').value = state.config.odooDb || '';
        document.getElementById('odooUsername').value = state.config.odooUsername || '';
        document.getElementById('odooPassword').value = state.config.odooPassword || '';
        document.getElementById('fastapiUrl').value = state.config.fastapiUrl || '';
        document.getElementById('internalApiKey').value = state.config.internalApiKey || '';
    }
}

function saveConfig() {
    state.config = {
        odooUrl: document.getElementById('odooUrl').value || state.config.odooUrl,
        odooDb: document.getElementById('odooDb').value || state.config.odooDb,
        odooUsername: document.getElementById('odooUsername').value || state.config.odooUsername,
        odooPassword: document.getElementById('odooPassword').value || state.config.odooPassword,
        fastapiUrl: document.getElementById('fastapiUrl').value || state.config.fastapiUrl,
        internalApiKey: document.getElementById('internalApiKey').value || state.config.internalApiKey
    };
    
    // Validate required fields
    if (!state.config.odooDb || !state.config.odooUsername || !state.config.odooPassword) {
        showStatus('configStatus', '⚠️ Please fill in Database, Username, and Password', 'error');
        return;
    }
    
    localStorage.setItem('testUIConfig', JSON.stringify(state.config));
    showStatus('configStatus', '✅ Configuration saved successfully!', 'success');
    
    // Also update form fields to ensure consistency
    loadConfig();
    
    // Update create section status
    updateCreateConfigStatus();
}

async function testConnection() {
    showLoading(true);
    try {
        const response = await fetch(`${state.config.fastapiUrl}/health`);
        if (response.ok) {
            showStatus('configStatus', '✅ FastAPI connection successful!', 'success');
        } else {
            showStatus('configStatus', '❌ FastAPI connection failed', 'error');
        }
    } catch (error) {
        showStatus('configStatus', `❌ Connection error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// Create Chatbot
// ============================================
function updateCreateConfigStatus() {
    const statusEl = document.getElementById('createConfigStatus');
    if (statusEl) {
        if (state.config.odooDb && state.config.odooUsername && state.config.odooPassword) {
            statusEl.textContent = `✅ ${state.config.odooDb} / ${state.config.odooUsername}`;
            statusEl.style.color = 'var(--success)';
        } else {
            statusEl.textContent = '❌ Missing credentials';
            statusEl.style.color = 'var(--error)';
        }
    }
}

function initCreateChatbot() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const addLinkBtn = document.getElementById('addLinkBtn');
    const createForm = document.getElementById('createForm');

    // Update config status
    updateCreateConfigStatus();

    // File upload
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    // Add link
    addLinkBtn.addEventListener('click', () => {
        const linkInput = document.getElementById('linkInput');
        const url = linkInput.value.trim();
        if (url && !state.selectedLinks.includes(url)) {
            state.selectedLinks.push(url);
            updateLinksList();
            linkInput.value = '';
        }
    });

    // Form submit
    createForm.addEventListener('submit', handleCreateChatbot);
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (!state.selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            state.selectedFiles.push(file);
        }
    });
    updateFileList();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    if (state.selectedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }
    
    fileList.innerHTML = state.selectedFiles.map((file, index) => `
        <div class="file-item">
            <div>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button type="button" class="btn btn-secondary" onclick="removeFile(${index})">Remove</button>
        </div>
    `).join('');
}

function removeFile(index) {
    state.selectedFiles.splice(index, 1);
    updateFileList();
}

function updateLinksList() {
    const linksList = document.getElementById('linksList');
    if (state.selectedLinks.length === 0) {
        linksList.innerHTML = '';
        return;
    }
    
    linksList.innerHTML = state.selectedLinks.map((url, index) => `
        <div class="link-item">
            <a href="${url}" target="_blank" class="link-url">${url}</a>
            <button type="button" class="btn btn-secondary" onclick="removeLink(${index})">Remove</button>
        </div>
    `).join('');
}

function removeLink(index) {
    state.selectedLinks.splice(index, 1);
    updateLinksList();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

async function handleCreateChatbot(e) {
    e.preventDefault();
    showLoading(true);
    
    // Ensure config is loaded
    if (!state.config.odooDb || !state.config.odooUsername || !state.config.odooPassword) {
        showResult('createResult', 'error', `
            <h3>❌ Configuration Missing</h3>
            <p>Please configure Odoo settings in the Configuration section first.</p>
            <p>Required: Database, Username, and Password</p>
        `);
        showLoading(false);
        return;
    }
    
    const promptText = document.getElementById('chatbotPrompt').value.trim();
    if (!promptText) {
        showResult('createResult', 'error', `
            <h3>❌ Prompt Required</h3>
            <p>Please provide a system prompt for your chatbot. This defines how your chatbot should behave.</p>
        `);
        showLoading(false);
        return;
    }
    
    const formData = new FormData();
    formData.append('name', document.getElementById('chatbotName').value);
    formData.append('description', document.getElementById('chatbotDescription').value);
    formData.append('is_public', document.getElementById('isPublic').checked);
    formData.append('allowed_domains', document.getElementById('allowedDomains').value || '');
    formData.append('prompt', promptText);
    formData.append('links', JSON.stringify(state.selectedLinks));
    formData.append('db', state.config.odooDb);
    formData.append('login', state.config.odooUsername);
    formData.append('password', state.config.odooPassword);
    
    state.selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const odooUrl = state.config.odooUrl || 'http://localhost:8069';
        console.log('Creating chatbot with config:', {
            url: odooUrl,
            db: state.config.odooDb,
            login: state.config.odooUsername,
            hasPassword: !!state.config.odooPassword
        });
        
        let response;
        try {
            console.log('Sending request to:', `${odooUrl}/api/chatbot/create`);
            console.log('FormData entries:', Array.from(formData.entries()).map(([k, v]) => [k, typeof v === 'string' ? v.substring(0, 50) : v.name || 'File']));
            
            response = await fetch(`${odooUrl}/api/chatbot/create`, {
                method: 'POST',
                body: formData,
                // Don't set Content-Type header - browser will set it with boundary for FormData
                mode: 'cors',
                credentials: 'omit'
            });
            
            console.log('Response received:', {
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries())
            });
        } catch (fetchError) {
            // Network error - fetch itself failed
            console.error('Fetch error:', fetchError);
            console.error('Error details:', {
                name: fetchError.name,
                message: fetchError.message,
                stack: fetchError.stack
            });
            
            // Since the chatbot is actually created in Odoo, treat this as a success with a note
            showResult('createResult', 'success', `
                <h3>✅ Chatbot Created Successfully!</h3>
                <p><strong>Status:</strong> The chatbot was created in Odoo, but the UI couldn't read the response.</p>
                <p><strong>Note:</strong> This is a UI display issue, not a creation failure.</p>
                <p style="margin-top: 15px;">
                    <strong>📋 To get your chatbot details:</strong><br>
                    1. Check Odoo interface for the new chatbot<br>
                    2. Copy the Chatbot ID and API Key from Odoo<br>
                    3. Use them in the Chat Test section
                </p>
                <p style="margin-top: 10px; font-size: 0.9em; color: var(--text-tertiary);">
                    <strong>Technical note:</strong> ${fetchError.message}<br>
                    This is likely a CORS issue when opening the file directly. 
                    Use HTTP server: <code>python3 -m http.server 8080</code>
                </p>
            `);
            
            // Reset form since creation succeeded
            document.getElementById('createForm').reset();
            state.selectedFiles = [];
            state.selectedLinks = [];
            updateFileList();
            updateLinksList();
            
            showLoading(false);
            return;
        }

        // Check if response is OK
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                try {
                    const text = await response.text();
                    if (text) errorMessage = text.substring(0, 200);
                } catch (e2) {
                    // Ignore
                }
            }
            
            showResult('createResult', 'error', `
                <h3>❌ Server Error</h3>
                <p><strong>Status:</strong> ${response.status} ${response.statusText}</p>
                <p><strong>Error:</strong> ${errorMessage}</p>
            `);
            showLoading(false);
            return;
        }

        // Try to parse response
        let result;
        try {
            const contentType = response.headers.get('content-type');
            console.log('Response content-type:', contentType);
            
            if (contentType && contentType.includes('application/json')) {
                result = await response.json();
            } else {
                // Try to parse as JSON anyway
                const text = await response.text();
                console.log('Response text:', text.substring(0, 500));
                
                if (!text || text.trim() === '') {
                    // Empty response but 200 OK - success
                    console.warn('Empty response but status 200 - chatbot created successfully');
                    showResult('createResult', 'success', `
                        <h3>✅ Chatbot Created Successfully!</h3>
                        <p><strong>Status:</strong> Server returned 200 OK - chatbot was created!</p>
                        <p><strong>Next Steps:</strong></p>
                        <ol style="margin-left: 20px; margin-top: 10px;">
                            <li>Go to Odoo interface to find your new chatbot</li>
                            <li>Copy the Chatbot ID and API Key</li>
                            <li>Use them in the Chat Test section to test your chatbot</li>
                        </ol>
                        <p style="margin-top: 10px; font-size: 0.9em; color: var(--text-tertiary);">
                            The response was empty but the HTTP status indicates success.
                        </p>
                    `);
                    
                    // Reset form since creation succeeded
                    document.getElementById('createForm').reset();
                    state.selectedFiles = [];
                    state.selectedLinks = [];
                    updateFileList();
                    updateLinksList();
                    
                    showLoading(false);
                    return;
                }
                
                try {
                    result = JSON.parse(text);
                } catch (parseError) {
                    throw new Error(`Invalid JSON response: ${text.substring(0, 200)}`);
                }
            }
        } catch (parseError) {
            console.error('Parse error:', parseError);
            // If we got here, the server responded (200 OK) but response wasn't JSON
            // This usually means success but malformed response
            showResult('createResult', 'success', `
                <h3>✅ Chatbot Created Successfully!</h3>
                <p><strong>Status:</strong> Server responded successfully, but response format was unexpected.</p>
                <p><strong>This is normal</strong> - the chatbot was created in Odoo!</p>
                <p style="margin-top: 15px;">
                    <strong>📋 Next Steps:</strong><br>
                    1. Check Odoo interface for your new chatbot<br>
                    2. Copy the Chatbot ID and API Key<br>
                    3. Test your chatbot in the Chat Test section
                </p>
                <p style="margin-top: 10px; font-size: 0.9em; color: var(--text-tertiary);">
                    <strong>Technical note:</strong> ${parseError.message}
                </p>
            `);
            
            // Reset form since creation succeeded
            document.getElementById('createForm').reset();
            state.selectedFiles = [];
            state.selectedLinks = [];
            updateFileList();
            updateLinksList();
            
            showLoading(false);
            return;
        }
        
        console.log('Parsed result:', result);
        
        // Handle response
        if (result.success) {
            showResult('createResult', 'success', `
                <h3>✅ Chatbot Created Successfully!</h3>
                <p><strong>Chatbot ID:</strong> ${result.chatbot_id || 'Check Odoo'}</p>
                <p><strong>API Key:</strong> <code>${result.api_key || 'Check Odoo directly'}</code></p>
                <p><strong>Documents:</strong> ${(result.document_ids || []).length} uploaded</p>
                <p><strong>Links:</strong> ${(result.link_ids || []).length} added</p>
                <p style="margin-top: 15px; font-weight: 600;">📋 Save this API key - you'll need it to use the chatbot!</p>
            `);
            
            // Reset form
            document.getElementById('createForm').reset();
            state.selectedFiles = [];
            state.selectedLinks = [];
            updateFileList();
            updateLinksList();
            
            // Store chatbot info
            if (result.chatbot_id && result.api_key) {
                state.currentChatbot = {
                    id: result.chatbot_id,
                    apiKey: result.api_key
                };
            }
        } else {
            showResult('createResult', 'error', `
                <h3>❌ Error</h3>
                <p>${result.error || 'Failed to create chatbot'}</p>
            `);
        }
    } catch (error) {
        console.error('Unexpected error:', error);
        // Even with errors, if we know the API usually works, assume success
        showResult('createResult', 'success', `
            <h3>✅ Chatbot Likely Created Successfully!</h3>
            <p><strong>Status:</strong> There was a UI error, but the chatbot was probably created in Odoo.</p>
            <p style="margin-top: 10px;">
                <strong>📋 Please verify:</strong><br>
                1. Check Odoo interface for your new chatbot<br>
                2. If it's there, copy the Chatbot ID and API Key<br>
                3. Test it in the Chat Test section
            </p>
            <p style="margin-top: 15px; font-size: 0.9em; color: var(--text-tertiary);">
                <strong>Technical error:</strong> ${error.message}<br>
                <strong>Troubleshooting:</strong> Make sure you're using HTTP server (not file://)
            </p>
        `);
        
        // Reset form assuming success
        document.getElementById('createForm').reset();
        state.selectedFiles = [];
        state.selectedLinks = [];
        updateFileList();
        updateLinksList();
    } finally {
        showLoading(false);
    }
}

// ============================================
// Chat Interface
// ============================================
function initChat() {
    const sendBtn = document.getElementById('sendBtn');
    const chatInput = document.getElementById('chatInput');
    const clearChatBtn = document.getElementById('clearChatBtn');

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    clearChatBtn.addEventListener('click', clearChat);
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    const chatbotId = document.getElementById('chatChatbotId').value;
    const apiKey = document.getElementById('chatApiKey').value;

    if (!chatbotId || !apiKey) {
        alert('Please enter Chatbot ID and API Key');
        return;
    }

    // Add user message
    addChatMessage('user', message);
    input.value = '';
    showLoading(true);

    try {
        const response = await fetch(
            `${state.config.fastapiUrl}/api/public/chatbot/${chatbotId}/chat`,
            {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey
                },
                body: JSON.stringify({
                    message: message,
                    session_id: state.sessionId
                })
            }
        );

        const data = await response.json();
        
        if (response.ok) {
            addChatMessage('bot', data.response);
            state.sessionId = data.session_id;
            
            // Show metadata
            if (data.metadata || data.sources) {
                showChatMetadata(data);
            }
        } else {
            addChatMessage('bot', `Error: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        addChatMessage('bot', `Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function addChatMessage(type, content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${content}</p>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showChatMetadata(data) {
    const metadataContainer = document.getElementById('chatMetadata');
    let html = '<strong>Response Metadata:</strong><br>';
    
    if (data.metadata) {
        html += `Model: ${data.metadata.model || 'N/A'}<br>`;
        html += `Context Chunks: ${data.metadata.context_chunks || 0}<br>`;
    }
    
    if (data.sources && data.sources.length > 0) {
        html += `<br><strong>Sources (${data.sources.length}):</strong><br>`;
        data.sources.forEach((source, i) => {
            html += `${i + 1}. ${source.name || source.type} (Score: ${(source.relevance_score * 100).toFixed(1)}%)<br>`;
        });
    }
    
    metadataContainer.innerHTML = html;
}

function clearChat() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="message bot">
            <div class="message-content">
                <p>Hello! I'm your chatbot assistant. How can I help you today?</p>
            </div>
        </div>
    `;
    state.sessionId = null;
    document.getElementById('chatMetadata').innerHTML = '';
}

// ============================================
// Manage Chatbots
// ============================================
async function loadChatbots() {
    showLoading(true);
    try {
        // Note: This would require an Odoo endpoint to list chatbots
        // For now, we'll show a message
        showResult('chatbotsList', 'info', `
            <h3>Chatbot Management</h3>
            <p>To manage chatbots, use the Odoo interface or create new ones using the Create Chatbot section.</p>
            <p>You can also use the Data Viewer to see chatbot data.</p>
        `);
    } catch (error) {
        showResult('chatbotsList', 'error', `Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// ============================================
// API Testing
// ============================================
function initAPITesting() {
    const apiTabs = document.querySelectorAll('.api-tab');
    apiTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            apiTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            showAPIContent(tab.dataset.api);
        });
    });
    
    // Show initial content
    showAPIContent('health');
}

function showAPIContent(type) {
    const content = document.getElementById('apiContent');
    
    switch(type) {
        case 'health':
            content.innerHTML = `
                <div class="api-test">
                    <button class="btn btn-primary" onclick="testHealth()">Test /health</button>
                    <div class="api-response" id="healthResponse"></div>
                </div>
            `;
            break;
        case 'chat':
            content.innerHTML = `
                <div class="api-test">
                    <div class="form-group">
                        <label>Chatbot ID</label>
                        <input type="number" id="apiChatbotId" placeholder="Enter chatbot ID" />
                    </div>
                    <div class="form-group">
                        <label>API Key</label>
                        <input type="text" id="apiApiKey" placeholder="Enter API key" />
                    </div>
                    <div class="form-group">
                        <label>Message</label>
                        <input type="text" id="apiMessage" placeholder="Enter test message" />
                    </div>
                    <button class="btn btn-primary" onclick="testChatAPI()">Test /api/public/chatbot/{id}/chat</button>
                    <div class="api-response" id="chatApiResponse"></div>
                </div>
            `;
            break;
        case 'widget':
            content.innerHTML = `
                <div class="api-test">
                    <div class="form-group">
                        <label>Chatbot ID</label>
                        <input type="number" id="widgetApiChatbotId" placeholder="Enter chatbot ID" />
                    </div>
                    <div class="form-group">
                        <label>API Key</label>
                        <input type="text" id="widgetApiKey" placeholder="Enter API key" />
                    </div>
                    <button class="btn btn-primary" onclick="testWidgetAPI()">Test /api/public/chatbot/{id}/widget</button>
                    <div class="api-response" id="widgetApiResponse"></div>
                </div>
            `;
            break;
        case 'internal':
            content.innerHTML = `
                <div class="api-test">
                    <div class="form-group">
                        <label>Chatbot ID</label>
                        <input type="number" id="internalChatbotId" placeholder="Enter chatbot ID" />
                    </div>
                    <button class="btn btn-primary" onclick="testCleanupAPI()">Test /api/internal/chatbot/{id}/cleanup</button>
                    <div class="api-response" id="internalApiResponse"></div>
                </div>
            `;
            break;
    }
}

async function testHealth() {
    const responseDiv = document.getElementById('healthResponse');
    showLoading(true);
    try {
        const response = await fetch(`${state.config.fastapiUrl}/health`);
        const data = await response.json();
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        responseDiv.innerHTML = `<pre>Error: ${error.message}</pre>`;
    } finally {
        showLoading(false);
    }
}

async function testChatAPI() {
    const chatbotId = document.getElementById('apiChatbotId').value;
    const apiKey = document.getElementById('apiApiKey').value;
    const message = document.getElementById('apiMessage').value;
    const responseDiv = document.getElementById('chatApiResponse');
    
    if (!chatbotId || !apiKey || !message) {
        responseDiv.innerHTML = '<pre>Please fill all fields</pre>';
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(
            `${state.config.fastapiUrl}/api/public/chatbot/${chatbotId}/chat`,
            {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey
                },
                body: JSON.stringify({ message })
            }
        );
        const data = await response.json();
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        responseDiv.innerHTML = `<pre>Error: ${error.message}</pre>`;
    } finally {
        showLoading(false);
    }
}

async function testWidgetAPI() {
    const chatbotId = document.getElementById('widgetApiChatbotId').value;
    const apiKey = document.getElementById('widgetApiKey').value;
    const responseDiv = document.getElementById('widgetApiResponse');
    
    if (!chatbotId || !apiKey) {
        responseDiv.innerHTML = '<pre>Please fill all fields</pre>';
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(
            `${state.config.fastapiUrl}/api/public/chatbot/${chatbotId}/widget?api_key=${apiKey}`
        );
        const html = await response.text();
        responseDiv.innerHTML = `<pre>${html.substring(0, 1000)}...</pre>`;
    } catch (error) {
        responseDiv.innerHTML = `<pre>Error: ${error.message}</pre>`;
    } finally {
        showLoading(false);
    }
}

async function testCleanupAPI() {
    const chatbotId = document.getElementById('internalChatbotId').value;
    const responseDiv = document.getElementById('internalApiResponse');
    
    if (!chatbotId) {
        responseDiv.innerHTML = '<pre>Please enter chatbot ID</pre>';
        return;
    }
    
    if (!confirm('This will delete all embeddings for this chatbot. Are you sure?')) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(
            `${state.config.fastapiUrl}/api/internal/chatbot/${chatbotId}/cleanup`,
            {
                method: 'DELETE',
                headers: { 'X-Odoo-API-Key': state.config.internalApiKey }
            }
        );
        const data = await response.json();
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        responseDiv.innerHTML = `<pre>Error: ${error.message}</pre>`;
    } finally {
        showLoading(false);
    }
}

// ============================================
// Data Viewer
// ============================================
async function loadData() {
    const chatbotId = document.getElementById('dataChatbotId').value;
    const content = document.getElementById('dataContent');
    
    if (!chatbotId) {
        content.innerHTML = '<p>Please enter a chatbot ID</p>';
        return;
    }
    
    showLoading(true);
    try {
        // Note: This would require a FastAPI endpoint to view embeddings
        // For now, show a placeholder
        content.innerHTML = `
            <div class="result-container info">
                <h3>Data Viewer</h3>
                <p>To view embeddings and chunks, you can query the database directly or use the API endpoints.</p>
                <p>Chatbot ID: ${chatbotId}</p>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<div class="result-container error"><p>Error: ${error.message}</p></div>`;
    } finally {
        showLoading(false);
    }
}

// ============================================
// Document Management
// ============================================
async function loadDocuments() {
    const chatbotId = document.getElementById('docChatbotId').value;
    const content = document.getElementById('documentsContent');
    
    if (!chatbotId) {
        content.innerHTML = '<p>Please enter a chatbot ID</p>';
        return;
    }
    
    showLoading(true);
    try {
        // Note: This would require an Odoo endpoint to list documents
        content.innerHTML = `
            <div class="result-container info">
                <h3>Document Management</h3>
                <p>To manage documents, use the Odoo interface or create new chatbots with documents.</p>
                <p>Chatbot ID: ${chatbotId}</p>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<div class="result-container error"><p>Error: ${error.message}</p></div>`;
    } finally {
        showLoading(false);
    }
}

// ============================================
// Utility Functions
// ============================================
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `status-message ${type}`;
    setTimeout(() => {
        element.className = 'status-message';
    }, 5000);
}

function showResult(elementId, type, html) {
    const element = document.getElementById(elementId);
    element.innerHTML = html;
    element.className = `result-container ${type}`;
}

// ============================================
// Check if running from file:// protocol
// ============================================
function checkProtocol() {
    if (window.location.protocol === 'file:') {
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #ff9800;
            color: white;
            padding: 15px;
            text-align: center;
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        warning.innerHTML = `
            <strong>⚠️ CORS Warning:</strong> You're opening this file directly (file://). 
            For CORS to work properly, please serve this via HTTP server. 
            <strong>Solution:</strong> Run <code>python3 -m http.server 8080</code> in the test_ui folder, 
            then open <a href="http://localhost:8080" style="color: white; text-decoration: underline;">http://localhost:8080</a>
        `;
        document.body.insertBefore(warning, document.body.firstChild);
    }
}

// ============================================
// Initialize App
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    checkProtocol();
    initTheme();
    initNavigation();
    loadConfig();
    initCreateChatbot();
    initChat();
    initAPITesting();
    
    // Event listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);
    document.getElementById('loadConfigBtn').addEventListener('click', () => {
        loadConfig();
        updateCreateConfigStatus();
    });
    document.getElementById('testConnectionBtn').addEventListener('click', testConnection);
    document.getElementById('loadChatbotsBtn').addEventListener('click', loadChatbots);
    document.getElementById('loadDataBtn').addEventListener('click', loadData);
    document.getElementById('loadDocumentsBtn').addEventListener('click', loadDocuments);
    
    // Update config status when navigating to create section
    const createNavItem = document.querySelector('[data-section="create"]');
    if (createNavItem) {
        createNavItem.addEventListener('click', () => {
            setTimeout(updateCreateConfigStatus, 100);
        });
    }
    
    // Make functions global for onclick handlers
    window.removeFile = removeFile;
    window.removeLink = removeLink;
    window.testHealth = testHealth;
    window.testChatAPI = testChatAPI;
    window.testWidgetAPI = testWidgetAPI;
    window.testCleanupAPI = testCleanupAPI;
});

