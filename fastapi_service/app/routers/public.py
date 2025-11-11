import logging
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import ChatRequest, ChatResponse, HealthResponse, ErrorResponse
from app.services.auth_service import auth_service
from app.services.rag_service import rag_service
from app.services.vector_store import vector_store

_logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


async def validate_chatbot_access(
    chatbot_id: int,
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key")
) -> dict:
    """Validate API key and get chatbot info"""
    # Get API key from header or query params
    api_key = x_api_key or request.query_params.get("api_key")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate API key with Odoo
    chatbot_info = await auth_service.validate_api_key(chatbot_id, api_key)
    
    if not chatbot_info:
        raise HTTPException(status_code=403, detail="Invalid API key or chatbot not found")
    
    # Check domain restrictions
    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    
    if not auth_service.validate_domain(chatbot_info, origin, referer):
        raise HTTPException(status_code=403, detail="Domain not allowed")
    
    return chatbot_info


@router.post("/chatbot/{chatbot_id}/chat", response_model=ChatResponse)
@limiter.limit("100/minute")
async def chat_with_chatbot(
    chatbot_id: int,
    chat_request: ChatRequest,
    request: Request,
    chatbot_info: dict = Depends(validate_chatbot_access)
):
    """Chat with a chatbot"""
    try:
        # Generate response using RAG
        response = await rag_service.generate_response(
            chatbot_id=chatbot_id,
            message=chat_request.message,
            chatbot_info=chatbot_info,
            session_id=chat_request.session_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        _logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chatbot/{chatbot_id}/widget")
@limiter.limit("60/minute")
async def get_chatbot_widget(
    chatbot_id: int,
    request: Request,
    chatbot_info: dict = Depends(validate_chatbot_access)
):
    """Get chatbot widget HTML"""
    try:
        # Generate widget HTML
        widget_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chatbot Widget</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f5;
                }}
                .chat-container {{
                    max-width: 400px;
                    height: 500px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }}
                .chat-header {{
                    background: #007bff;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    font-weight: bold;
                }}
                .chat-messages {{
                    flex: 1;
                    padding: 15px;
                    overflow-y: auto;
                }}
                .chat-input {{
                    padding: 15px;
                    border-top: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                }}
                .chat-input input {{
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    outline: none;
                }}
                .chat-input button {{
                    padding: 10px 15px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }}
                .message {{
                    margin-bottom: 15px;
                    padding: 10px;
                    border-radius: 10px;
                    max-width: 80%;
                }}
                .message.user {{
                    background: #007bff;
                    color: white;
                    margin-left: auto;
                }}
                .message.bot {{
                    background: #f1f1f1;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    {chatbot_info.get('name', 'Chatbot')}
                </div>
                <div class="chat-messages" id="messages">
                    <div class="message bot">
                        Hello! How can I help you today?
                    </div>
                </div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Type your message...">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <script>
                const chatbotId = {chatbot_id};
                const apiKey = '{request.query_params.get("api_key", "")}';
                let sessionId = null;
                
                async function sendMessage() {{
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    // Add user message to chat
                    addMessage(message, 'user');
                    input.value = '';
                    
                    try {{
                        const response = await fetch(`/api/public/chatbot/${{chatbotId}}/chat`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'X-API-Key': apiKey
                            }},
                            body: JSON.stringify({{
                                message: message,
                                session_id: sessionId
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        if (response.ok) {{
                            sessionId = data.session_id;
                            addMessage(data.response, 'bot');
                        }} else {{
                            addMessage('Sorry, I encountered an error.', 'bot');
                        }}
                    }} catch (error) {{
                        addMessage('Sorry, I encountered an error.', 'bot');
                    }}
                }}
                
                function addMessage(text, sender) {{
                    const messages = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${{sender}}`;
                    messageDiv.textContent = text;
                    messages.appendChild(messageDiv);
                    messages.scrollTop = messages.scrollHeight;
                }}
                
                // Send message on Enter key
                document.getElementById('messageInput').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        sendMessage();
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return widget_html
        
    except Exception as e:
        _logger.error(f"Error generating widget: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chatbot/{chatbot_id}/health", response_model=HealthResponse)
async def chatbot_health_check(chatbot_id: int):
    """Health check for a specific chatbot (no auth required)"""
    try:
        # Get embeddings count
        embeddings_count = await vector_store.get_embeddings_count(chatbot_id)
        
        return HealthResponse(
            status="healthy",
            chatbot_id=chatbot_id,
            chatbot_status="unknown",  # Would need to check with Odoo
            embeddings_count=embeddings_count
        )
        
    except Exception as e:
        _logger.error(f"Error in health check: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            chatbot_id=chatbot_id,
            error=str(e)
        )
