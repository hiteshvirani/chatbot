# Testing UI

Simple testing interface for the chatbot platform.

## Files

- **`index.html`** - Chat testing UI for testing existing chatbots
- **`create.html`** - Simple UI for creating new chatbots with documents and links
- **`styles.css`** - Shared styles
- **`script.js`** - Chat testing functionality  
- **`create-script.js`** - Chatbot creation functionality

## Usage

### Creating a Chatbot

1. Open `create.html`
2. Enter your Odoo credentials:
   - Database name (e.g., `odoo_cb`)
   - Username (e.g., `admin`) 
   - Password
3. Fill in chatbot details
4. Upload documents (PDF, DOCX, TXT)
5. Add links
6. Click "Create Chatbot"
7. Save the generated API key

### Testing a Chatbot

1. Open `index.html`
2. Go to Configuration tab
3. Enter the chatbot ID and API key
4. Use the Chat Test tab to interact with the chatbot

## Features

- **Simple UI** - No complex authentication flows
- **File Upload** - Drag & drop or click to upload documents
- **Link Management** - Add multiple URLs for content scraping
- **Direct Integration** - Connects directly to Odoo backend
- **Real-time Testing** - Test chatbots immediately after creation

## Requirements

- Odoo service running on port 8069
- FastAPI service running on port 8000
- Valid Odoo database with the chatbot module installed