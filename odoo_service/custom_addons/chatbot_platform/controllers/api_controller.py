import json
import logging
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

    @http.route('/api/chatbot/<int:chatbot_id>/info', type='json', auth='none', methods=['GET'], csrf=False)
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
