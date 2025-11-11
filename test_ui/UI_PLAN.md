# Test UI Plan - Comprehensive Testing Interface

## Overview
A single, comprehensive testing UI that allows testing all chatbot platform features with a clean, simple design and dark/light theme support.

## Features to Test

### 1. Configuration Section
- Odoo URL, Database, Username, Password
- FastAPI URL
- Default settings storage (localStorage)
- Theme toggle (Dark/Light)

### 2. Create Chatbot Section
- Chatbot name, description
- Public/Private toggle
- Allowed domains
- File upload (drag & drop)
- Link management (add/remove)
- Real-time feedback
- Display created chatbot ID and API key

### 3. Chat Interface Section
- Chatbot ID and API key input
- Chat message interface
- Message history
- Session management
- Source display (from RAG)
- Response metadata

### 4. Manage Chatbots Section
- List all chatbots
- View chatbot details
- Update chatbot
- Delete chatbot (with cleanup verification)
- View documents and links

### 5. API Testing Section
- Health check
- Chat endpoint test
- Widget endpoint test
- Internal endpoints (with auth)
- Request/Response viewer
- Error handling display

### 6. Data Viewer Section
- View embeddings (by chatbot_id)
- View chunks
- View sessions
- Statistics and counts
- Search/filter capabilities

### 7. Document Management Section
- Upload new documents to existing chatbot
- Update document content
- Delete documents
- View sync status

## UI Design Principles

### Layout
- **Header**: Title, theme toggle, quick actions
- **Sidebar/Tabs**: Navigation between sections
- **Main Content**: Section-specific content
- **Footer**: Status, version info

### Theme System
- **Light Theme**: 
  - Background: #ffffff, #f5f5f5
  - Text: #333333, #666666
  - Primary: #667eea, #764ba2
  - Accent: #4CAF50, #f44336
  
- **Dark Theme**:
  - Background: #1a1a1a, #2d2d2d
  - Text: #e0e0e0, #b0b0b0
  - Primary: #8b9aff, #a78bfa
  - Accent: #66bb6a, #ef5350

### Components
- Cards for sections
- Buttons with clear states
- Input fields with validation
- Status indicators
- Loading states
- Error/success messages
- Code viewers for API responses

## Technical Implementation

### File Structure
```
test_ui/
├── index.html          (Main UI - single page)
├── styles.css          (All styles with theme support)
└── app.js              (All JavaScript functionality)
```

### Key Functions
- Theme management (localStorage)
- API client (Odoo & FastAPI)
- State management
- Error handling
- Response formatting
- Data visualization

### Storage
- localStorage for:
  - Theme preference
  - Configuration
  - Recent chatbots
  - Session data

## User Flow

1. **First Time**: Configure Odoo credentials
2. **Create**: Create a chatbot with documents/links
3. **Test**: Chat with the chatbot
4. **Manage**: View, update, or delete chatbots
5. **Debug**: Use API testing and data viewer for troubleshooting

## Responsive Design
- Mobile-friendly
- Tablet-optimized
- Desktop-optimized
- Collapsible sections
- Adaptive layouts

