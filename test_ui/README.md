# Chatbot Platform - Test UI

A comprehensive, modern testing interface for the Chatbot Platform with dark/light theme support.

## Features

### 🎨 Modern UI
- **Dark/Light Theme**: Toggle between themes with one click
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Clean Interface**: Simple, intuitive design
- **Real-time Feedback**: Clear status messages and loading indicators

### 📋 Sections

#### 1. ⚙️ Configuration
- Configure Odoo connection (URL, database, credentials)
- Configure FastAPI URL
- Set internal API key
- Save/load configuration (persisted in browser)
- Test connection to services

#### 2. ➕ Create Chatbot
- Create new chatbots with:
  - Name and description
  - Public/private settings
  - Allowed domains
  - Document upload (PDF, DOCX, TXT)
  - Link management
- Drag & drop file upload
- Real-time file list
- Display created chatbot ID and API key

#### 3. 💬 Chat Test
- Interactive chat interface
- Test chatbot responses
- View response metadata
- See source documents used
- Session management
- Clear chat history

#### 4. 📋 Manage Chatbots
- View chatbot list (when endpoint available)
- Manage existing chatbots
- View chatbot details

#### 5. 🔌 API Testing
- **Health Check**: Test FastAPI health endpoint
- **Chat API**: Test chat endpoint with custom messages
- **Widget API**: Test widget endpoint
- **Internal APIs**: Test internal endpoints (cleanup, etc.)
- View request/response in formatted JSON

#### 6. 📊 Data Viewer
- View embeddings by chatbot ID
- View chunks and metadata
- View statistics
- Search and filter capabilities

#### 7. 📄 Document Management
- View documents for a chatbot
- Upload new documents
- Update document content
- Delete documents

## Usage

### Getting Started

1. **Start HTTP Server (IMPORTANT for CORS)**
   ```bash
   # Option 1: Use the provided script
   cd test_ui
   ./start_server.sh
   
   # Option 2: Use Python directly
   cd test_ui
   python3 -m http.server 8080
   
   # Option 3: Use Node.js (if installed)
   cd test_ui
   npx http-server -p 8080
   ```

2. **Open in Browser**
   ```
   Open: http://localhost:8080
   ```
   
   ⚠️ **Important:** Do NOT open `index.html` directly (file://) - this will cause CORS errors!
   You MUST serve it via HTTP server for CORS to work properly.

2. **Configure Settings**
   - Go to Configuration section
   - Enter Odoo URL (default: http://localhost:8069)
   - Enter database name (default: odoo_c)
   - Enter username and password
   - Enter FastAPI URL (default: http://localhost:8000)
   - Click "Save Configuration"

3. **Create a Chatbot**
   - Go to Create Chatbot section
   - Enter chatbot name
   - Upload documents (optional)
   - Add links (optional)
   - Click "Create Chatbot"
   - **Save the API key** - you'll need it!

4. **Test Chat**
   - Go to Chat Test section
   - Enter Chatbot ID and API Key
   - Type a message and send
   - View response and metadata

5. **Test APIs**
   - Go to API Testing section
   - Select an endpoint to test
   - Fill in required fields
   - Click test button
   - View response

### Theme Toggle

Click the theme toggle button (🌙/☀️) in the header to switch between dark and light themes. Your preference is saved automatically.

### Configuration Persistence

All configuration is saved in your browser's localStorage:
- Theme preference
- Odoo credentials
- FastAPI URL
- Recent chatbots

## File Structure

```
test_ui/
├── index.html      # Main UI (single page application)
├── styles.css      # All styles with theme support
├── app.js          # All JavaScript functionality
├── UI_PLAN.md      # Planning document
└── README.md       # This file
```

## Requirements

- Modern browser (Chrome, Firefox, Safari, Edge)
- Odoo service running (default: http://localhost:8069)
- FastAPI service running (default: http://localhost:8000)
- Valid Odoo database with chatbot module installed

## Features in Detail

### File Upload
- **Supported formats**: PDF, DOCX, TXT
- **Drag & drop**: Drop files directly onto the upload area
- **Click to browse**: Click the upload area to select files
- **Multiple files**: Upload multiple files at once
- **File preview**: See file name and size before upload

### Chat Interface
- **Session management**: Maintains conversation context
- **Source display**: Shows which documents were used
- **Metadata**: Displays model, tokens, response time
- **Clear chat**: Reset conversation at any time

### API Testing
- **Health Check**: Verify FastAPI is running
- **Chat Endpoint**: Test chat functionality
- **Widget Endpoint**: Test widget generation
- **Internal Endpoints**: Test cleanup and other internal APIs
- **Response Viewer**: Formatted JSON display

## Troubleshooting

### Connection Issues
- Verify Odoo and FastAPI services are running
- Check URLs in Configuration section
- Test connection using "Test Connection" button

### File Upload Issues
- Ensure files are in supported formats (PDF, DOCX, TXT)
- Check file size (very large files may timeout)
- Verify Odoo service is accessible

### Chat Not Working
- Verify Chatbot ID and API Key are correct
- Check that chatbot has documents/links uploaded
- Ensure FastAPI service is running
- Check browser console for errors

### Theme Not Saving
- Clear browser cache and try again
- Check browser localStorage is enabled
- Try a different browser

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Opera (latest)

## Notes

- Configuration is stored locally in your browser
- API keys are displayed in plain text - keep them secure
- Some features require additional Odoo endpoints to be implemented
- The UI is designed for testing and development purposes

## Future Enhancements

- [ ] Real-time chatbot list from Odoo
- [ ] Embedding visualization
- [ ] Chunk viewer with search
- [ ] Document preview
- [ ] Batch operations
- [ ] Export/import configuration
- [ ] Advanced filtering and search
