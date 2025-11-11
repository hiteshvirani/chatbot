import json
import logging
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ChatbotAPIController(http.Controller):

    @http.route('/api/chatbot/validate', type='json', auth='none', methods=['POST'], csrf=False)
    def validate_api_key(self, **kwargs):
        """Validate API key for external access"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            chatbot_id = data.get('chatbot_id')
            api_key = data.get('api_key')
            
            if not chatbot_id or not api_key:
                return {'valid': False, 'error': 'Missing chatbot_id or api_key'}
            
            # Validate using the model method
            chatbot_model = request.env['chatbot.chatbot'].sudo()
            is_valid = chatbot_model.validate_api_key(chatbot_id, api_key)
            
            return {'valid': is_valid}
            
        except Exception as e:
            _logger.error(f"Error validating API key: {str(e)}")
            return {'valid': False, 'error': 'Internal error'}

    @http.route('/api/chatbot/<int:chatbot_id>/info', type='json', auth='none', methods=['GET', 'POST'], csrf=False)
    def get_chatbot_info(self, chatbot_id, **kwargs):
        """Get chatbot information for FastAPI"""
        try:
            chatbot = request.env['chatbot.chatbot'].sudo().browse(chatbot_id)
            
            if not chatbot.exists():
                return {'error': 'Chatbot not found'}
            
            return {
                'id': chatbot.id,
                'name': chatbot.name,
                'status': chatbot.status,
                'is_public': chatbot.is_public,
                'allowed_domains': chatbot.allowed_domains,
                'prompts': [{
                    'type': prompt.prompt_type,
                    'text': prompt.prompt_text,
                    'order': prompt.order
                } for prompt in chatbot.prompt_ids.filtered('is_active')]
            }
            
        except Exception as e:
            _logger.error(f"Error getting chatbot info: {str(e)}")
            return {'error': 'Internal error'}

    @http.route('/api/chatbot/<int:chatbot_id>/chat', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def chat_with_chatbot(self, chatbot_id, **kwargs):
        """Chat endpoint that adds prompts and forwards to FastAPI"""
        try:
            # Get request data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            message = data.get('message')
            api_key = data.get('api_key') or request.httprequest.headers.get('X-API-Key')
            session_id = data.get('session_id')
            
            if not message:
                return {'error': 'Message is required'}
            
            if not api_key:
                return {'error': 'API key is required'}
            
            # Validate API key
            chatbot_model = request.env['chatbot.chatbot'].sudo()
            is_valid = chatbot_model.validate_api_key(chatbot_id, api_key)
            
            if not is_valid:
                return {'error': 'Invalid API key or chatbot not found'}
            
            # Get chatbot
            chatbot = chatbot_model.browse(chatbot_id)
            if not chatbot.exists() or chatbot.status != 'active':
                return {'error': 'Chatbot not found or not active'}
            
            # Get user-level prompts from chatbot
            user_prompts = []
            for prompt in chatbot.prompt_ids.filtered('is_active'):
                if prompt.prompt_type == 'system':
                    user_prompts.append({
                        'type': 'system',
                        'text': prompt.prompt_text,
                        'order': prompt.order
                    })
            
            # Get FastAPI URL
            import os
            fastapi_url = os.getenv('FASTAPI_URL') or request.env['ir.config_parameter'].sudo().get_param('fastapi.url', 'http://localhost:8000')
            
            # Prepare request to FastAPI with user prompts only
            # Master prompt is now handled by FastAPI
            fastapi_payload = {
                'message': message,
                'session_id': session_id,
                'user_prompts': user_prompts  # User-level prompts only
            }
            
            # Forward to FastAPI
            response = requests.post(
                f"{fastapi_url}/api/public/chatbot/{chatbot_id}/chat",
                json=fastapi_payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': api_key
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"FastAPI error: {response.status_code} - {response.text}")
                return {'error': f'FastAPI error: {response.status_code}'}
                
        except Exception as e:
            _logger.error(f"Error in chat endpoint: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            return {'error': f'Internal error: {str(e)}'}

    @http.route('/api/chatbot/create', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def create_chatbot(self, **kwargs):
        """Create chatbot with documents and links in one API call"""
        # Handle CORS preflight
        if request.httprequest.method == 'OPTIONS':
            _logger.info("CORS preflight request received")
            response = request.make_response(
                '',
                headers=[
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With, Accept'),
                    ('Access-Control-Max-Age', '86400'),
                ],
                status=200
            )
            _logger.info("CORS preflight response sent")
            return response
        
        try:
            import base64
            import tempfile
            import os
            
            # Direct authentication - no session management for testing
            db = request.params.get('db')
            login = request.params.get('login')
            password = request.params.get('password')
            
            if not db or not login or not password:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Authentication required. Please provide db, login, and password.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=401
                )
            
            # Direct authentication using registry (no session calls)
            from odoo import registry
            from odoo.http import db_list
            
            if db not in db_list():
                return request.make_response(
                    json.dumps({'success': False, 'error': f'Database {db} not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Authenticate directly using registry - simple for testing
            try:
                registry_obj = registry(db)
                with registry_obj.cursor() as cr:
                    # Get user by login
                    cr.execute("SELECT id, password FROM res_users WHERE login = %s AND active = true", (login,))
                    user_data = cr.fetchone()
                    
                    if not user_data:
                        return request.make_response(
                            json.dumps({'success': False, 'error': 'Authentication failed. Invalid credentials.'}),
                            headers=[('Content-Type', 'application/json')],
                            status=401
                        )
                    
                    user_id, stored_password = user_data
                    
                    # Verify password using Odoo's password check
                    from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
                    import hashlib
                    import base64
                    import passlib.context
                    
                    # Use Odoo's password verification
                    env = request.env(cr=cr)
                    user = env['res.users'].browse(user_id)
                    if not user._crypt_context().verify(password, stored_password):
                        return request.make_response(
                            json.dumps({'success': False, 'error': 'Authentication failed. Invalid credentials.'}),
                            headers=[('Content-Type', 'application/json')],
                            status=401
                        )
                    
                    # Set environment with authenticated user (Odoo 18 way)
                    request.update_env(user=user_id)
            except Exception as e:
                _logger.error(f"Authentication error: {str(e)}")
                import traceback
                _logger.error(traceback.format_exc())
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Authentication failed. Please check your credentials.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=401
                )
            
            # Get form data
            name = request.params.get('name')
            description = request.params.get('description', '')
            is_public = request.params.get('is_public', 'true').lower() == 'true'
            allowed_domains = request.params.get('allowed_domains', '')
            
            if not name:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Chatbot name is required'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Validate prompt is required
            # Try both request.params and request.httprequest.form for form data
            prompt_text = request.params.get('prompt', '') or request.httprequest.form.get('prompt', '')
            prompt_text = prompt_text.strip() if prompt_text else ''
            
            if not prompt_text:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Prompt is required. Please provide a system prompt for your chatbot.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Create chatbot
            chatbot_vals = {
                'name': name,
                'description': description,
                'is_public': is_public,
                'allowed_domains': allowed_domains if allowed_domains else False,
                'status': 'draft',
                'user_id': request.env.user.id
            }
            
            chatbot = request.env['chatbot.chatbot'].create(chatbot_vals)
            
            # Generate API key
            api_key = chatbot.generate_api_key()
            
            # Handle file uploads
            document_ids = []
            uploaded_files = request.httprequest.files.getlist('files')
            
            for uploaded_file in uploaded_files:
                if uploaded_file.filename:
                    # Save file temporarily
                    file_ext = os.path.splitext(uploaded_file.filename)[1][1:].lower()
                    file_type_map = {'pdf': 'pdf', 'docx': 'docx', 'txt': 'txt'}
                    file_type = file_type_map.get(file_ext, 'txt')
                    
                    # Read file content
                    file_content = uploaded_file.read()
                    
                    # Create attachment
                    attachment = request.env['ir.attachment'].create({
                        'name': uploaded_file.filename,
                        'type': 'binary',
                        'datas': base64.b64encode(file_content),
                        'res_model': 'chatbot.document',
                        'res_id': 0
                    })
                    
                    # Create document record
                    doc_vals = {
                        'chatbot_id': chatbot.id,
                        'name': uploaded_file.filename,
                        'file_type': file_type,
                        'file_size': len(file_content),
                        'file_path': attachment.store_fname if hasattr(attachment, 'store_fname') else None
                    }
                    
                    doc = request.env['chatbot.document'].create(doc_vals)
                    
                    # Extract content from file
                    if file_type == 'pdf':
                        import PyPDF2
                        from io import BytesIO
                        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
                        content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
                    elif file_type == 'docx':
                        from docx import Document
                        from io import BytesIO
                        docx = Document(BytesIO(file_content))
                        content = '\n'.join([para.text for para in docx.paragraphs])
                    else:
                        content = file_content.decode('utf-8', errors='ignore')
                    
                    if content:
                        doc.write({'content': content})
                        doc.sync_to_fastapi()
                    
                    document_ids.append(doc.id)
            
            # Handle links
            link_ids = []
            links_json = request.params.get('links', '[]')
            try:
                links = json.loads(links_json) if isinstance(links_json, str) else links_json
            except:
                links = []
            
            for link_url in links:
                if link_url:
                    link_vals = {
                        'chatbot_id': chatbot.id,
                        'url': link_url
                    }
                    link = request.env['chatbot.link'].create(link_vals)
                    link_ids.append(link.id)
            
            # Handle prompt (required)
            prompt_vals = {
                'chatbot_id': chatbot.id,
                'prompt_text': prompt_text,
                'prompt_type': 'system',
                'order': 10,
                'is_active': True
            }
            prompt = request.env['chatbot.prompt'].create(prompt_vals)
            
            # Prepare response data
            response_data = {
                'success': True,
                'chatbot_id': chatbot.id,
                'api_key': api_key,
                'document_ids': document_ids,
                'link_ids': link_ids
            }
            response_json = json.dumps(response_data)
            
            _logger.info(f"Returning response: {response_json}")
            
            return request.make_response(
                response_json,
                headers=[
                    ('Content-Type', 'application/json; charset=utf-8'),
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With'),
                    ('Access-Control-Allow-Credentials', 'false'),
                ],
                status=200
            )
            
        except Exception as e:
            _logger.error(f"Error creating chatbot: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type'),
                ],
                status=500
            )
