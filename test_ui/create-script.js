let selectedFiles = [];
let selectedLinks = [];

// Load saved config
const config = {
    odooUrl: localStorage.getItem('odooUrl') || 'http://localhost:8069',
    database: localStorage.getItem('odooDb') || '',
    username: localStorage.getItem('odooUsername') || '',
    password: localStorage.getItem('odooPassword') || ''
};

document.getElementById('odooUrl').value = config.odooUrl;
document.getElementById('odooDb').value = config.database;
document.getElementById('odooUsername').value = config.username;

// File Upload
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

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

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    updateFileList();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    if (selectedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }

    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <div>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button type="button" class="remove-btn" onclick="removeFile(${index})">Remove</button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

window.removeFile = removeFile;

// Links
document.getElementById('addLinkBtn').addEventListener('click', () => {
    const linkInput = document.getElementById('linkInput');
    const url = linkInput.value.trim();
    
    if (!url) {
        alert('Please enter a URL');
        return;
    }

    if (!selectedLinks.includes(url)) {
        selectedLinks.push(url);
        updateLinksList();
        linkInput.value = '';
    } else {
        alert('This link is already added');
    }
});

function updateLinksList() {
    const linksList = document.getElementById('linksList');
    if (selectedLinks.length === 0) {
        linksList.innerHTML = '';
        return;
    }

    linksList.innerHTML = selectedLinks.map((url, index) => `
        <div class="link-item">
            <a href="${url}" target="_blank" class="link-url">${url}</a>
            <button type="button" class="remove-btn" onclick="removeLink(${index})">Remove</button>
        </div>
    `).join('');
}

function removeLink(index) {
    selectedLinks.splice(index, 1);
    updateLinksList();
}

window.removeLink = removeLink;

// No separate authentication needed - credentials sent with request

// Form Submit
document.getElementById('createForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    const messageDiv = document.getElementById('message');
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';
    messageDiv.innerHTML = '';

    try {
        // Authentication is handled in the request via credentials

        // Prepare FormData
        const formData = new FormData();
        formData.append('name', document.getElementById('chatbotName').value);
        formData.append('description', document.getElementById('description').value);
        formData.append('is_public', document.getElementById('isPublic').checked);
        formData.append('allowed_domains', document.getElementById('allowedDomains').value || '');
        formData.append('links', JSON.stringify(selectedLinks));
        
        // Add authentication credentials
        formData.append('db', document.getElementById('odooDb').value);
        formData.append('login', document.getElementById('odooUsername').value);
        formData.append('password', document.getElementById('odooPassword').value);

        // Add files
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        const odooUrl = document.getElementById('odooUrl').value;
        
        // Create chatbot - credentials sent directly in form data (no separate auth needed)
        console.log('Sending request to:', `${odooUrl}/api/chatbot/create`);
        console.log('Form data entries:', Array.from(formData.entries()));
        
        let response;
        try {
            response = await fetch(`${odooUrl}/api/chatbot/create`, {
                method: 'POST',
                body: formData
            });
            console.log('Response received:', response.status, response.statusText);
        } catch (fetchError) {
            // Network error - fetch itself failed
            console.error('Fetch error:', fetchError);
            throw new Error(`Network error: ${fetchError.message}. Make sure Odoo is running at ${odooUrl}`);
        }

        // Check if response is OK
        if (!response.ok) {
            console.error('Response not OK:', response.status, response.statusText);
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                console.error('Error response data:', errorData);
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                try {
                    const text = await response.text();
                    console.error('Error response text:', text);
                    if (text) {
                        errorMessage = text;
                    }
                } catch (textError) {
                    console.error('Could not read error response:', textError);
                }
            }
            throw new Error(errorMessage);
        }

        // Parse JSON response
        let result;
        try {
            // Check content type
            const contentType = response.headers.get('content-type');
            console.log('Response content-type:', contentType);
            
            // Try to parse as JSON directly first
            result = await response.json();
            console.log('Parsed JSON result:', result);
        } catch (parseError) {
            // If that fails, try reading as text
            console.error('JSON parse error, trying text:', parseError);
            try {
                const responseText = await response.text();
                console.log('Response as text:', responseText);
                if (!responseText || responseText.trim() === '') {
                    // Empty response but 200 OK - this might be the issue
                    console.warn('Empty response but status 200 - assuming success');
                    result = { success: true, message: 'Chatbot created (empty response)' };
                } else {
                    result = JSON.parse(responseText);
                }
            } catch (textParseError) {
                console.error('Text parse error:', textParseError);
                throw new Error(`Invalid response from server: ${textParseError.message}`);
            }
        }

        if (result.success) {
            messageDiv.innerHTML = `
                <div class="message success">
                    <h3>✅ Chatbot Created Successfully!</h3>
                    <p><strong>Chatbot ID:</strong> ${result.chatbot_id || 'Unknown'}</p>
                    <p><strong>API Key:</strong> <code style="background: #f0f0f0; padding: 5px 10px; border-radius: 5px; display: inline-block; margin-top: 5px;">${result.api_key || 'Check Odoo directly'}</code></p>
                    <p style="margin-top: 15px; font-weight: 600;">📋 Save this API key - you'll need it to use the chatbot!</p>
                    <p style="margin-top: 10px;"><strong>Documents:</strong> ${(result.document_ids || []).length} uploaded</p>
                    <p><strong>Links:</strong> ${(result.link_ids || []).length} added</p>
                </div>
            `;
            
            // Reset form
            document.getElementById('createForm').reset();
            selectedFiles = [];
            selectedLinks = [];
            updateFileList();
            updateLinksList();
        } else {
            throw new Error(result.error || 'Failed to create chatbot');
        }
    } catch (error) {
        console.error('Error creating chatbot:', error);
        let errorMsg = error.message || 'Unknown error';
        
        // More specific error messages
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
            errorMsg = `Network error: Could not connect to Odoo at ${document.getElementById('odooUrl').value}. Make sure Odoo is running and accessible.`;
        } else if (errorMsg.includes('CORS')) {
            errorMsg = 'CORS error: Browser blocked the request. Check Odoo CORS settings.';
        } else if (errorMsg.includes('Empty response')) {
            errorMsg = 'Server returned empty response. The request may have succeeded - check Odoo to verify.';
        } else if (errorMsg.includes('Invalid response')) {
            errorMsg = `Server response error: ${errorMsg}`;
        }
        
        messageDiv.innerHTML = `
            <div class="message error">
                <h3>❌ Error</h3>
                <p><strong>${errorMsg}</strong></p>
                <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    <strong>Note:</strong> If the chatbot was created successfully in Odoo, you can ignore this error and check Odoo directly.
                </p>
                <p style="margin-top: 10px; font-size: 0.9em;">
                    Please check:
                    <ul style="margin-top: 10px; padding-left: 20px;">
                        <li>Odoo URL is correct (e.g., http://localhost:8069)</li>
                        <li>Database name is correct (e.g., odoo_c)</li>
                        <li>Username and password are correct</li>
                        <li>Odoo service is running</li>
                        <li>Check browser console (F12) for more details</li>
                    </ul>
                </p>
            </div>
        `;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Chatbot';
    }
});

