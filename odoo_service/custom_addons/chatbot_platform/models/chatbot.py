import hashlib
import secrets
import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChatbotChatbot(models.Model):
    _name = 'chatbot.chatbot'
    _description = 'Chatbot Configuration'
    _order = 'created_at desc'

    name = fields.Char('Chatbot Name', required=True)
    user_id = fields.Many2one('res.users', 'Owner', required=True, default=lambda self: self.env.user)
    description = fields.Text('Description')
    
    # API Key fields
    api_key_hash = fields.Char('API Key Hash', readonly=True)
    api_key_prefix = fields.Char('API Key Prefix', readonly=True)
    api_key_display = fields.Char('API Key', compute='_compute_api_key_display', store=False)
    
    # Configuration
    is_public = fields.Boolean('Public Access', default=True)
    allowed_domains = fields.Text('Allowed Domains', help='Comma-separated list of allowed domains')
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='draft', required=True)
    
    # Relationships
    document_ids = fields.One2many('chatbot.document', 'chatbot_id', 'Documents')
    link_ids = fields.One2many('chatbot.link', 'chatbot_id', 'Links')
    prompt_ids = fields.One2many('chatbot.prompt', 'chatbot_id', 'Prompts')
    
    # Computed fields
    document_count = fields.Integer('Documents', compute='_compute_counts')
    link_count = fields.Integer('Links', compute='_compute_counts')
    embed_code = fields.Text('Embed Code', compute='_compute_embed_code')
    
    # Timestamps
    created_at = fields.Datetime('Created At', default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime('Updated At', default=fields.Datetime.now)

    @api.depends('document_ids', 'link_ids')
    def _compute_counts(self):
        for record in self:
            record.document_count = len(record.document_ids)
            record.link_count = len(record.link_ids)

    @api.depends('api_key_prefix')
    def _compute_api_key_display(self):
        for record in self:
            if record.api_key_prefix:
                record.api_key_display = f"{record.api_key_prefix}..."
            else:
                record.api_key_display = "Not generated"

    @api.depends('id', 'api_key_hash')
    def _compute_embed_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8000')
        for record in self:
            if record.id and record.api_key_hash:
                # Generate iframe embed code
                iframe_code = f'''<iframe 
  src="{base_url}/api/public/chatbot/{record.id}/widget?api_key=YOUR_API_KEY_HERE..."
  width="400"
  height="600"
  frameborder="0"
  style="border: none; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
</iframe>'''
                record.embed_code = iframe_code
            else:
                record.embed_code = "Save the chatbot first to generate embed code"

    @api.model
    def create(self, vals):
        # Generate API key on creation
        chatbot = super().create(vals)
        chatbot.generate_api_key()
        return chatbot

    def write(self, vals):
        vals['updated_at'] = fields.Datetime.now()
        return super().write(vals)

    def generate_api_key(self):
        """Generate a new API key for the chatbot"""
        # Generate: YOUR_API_KEY_HERE{32_random_chars}
        random_part = secrets.token_urlsafe(32)[:32]  # Ensure exactly 32 chars
        api_key = f"YOUR_API_KEY_HERE{random_part}"
        
        # Hash for storage (never store plain text)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store hash and prefix
        self.write({
            'api_key_hash': key_hash,
            'api_key_prefix': api_key[:12]  # Store first 12 chars for display
        })
        
        # Return the plain key only once for user to copy
        return api_key

    def action_regenerate_api_key(self):
        """Action to regenerate API key"""
        new_key = self.generate_api_key()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'API Key Regenerated',
                'message': f'New API Key: {new_key}\nPlease copy and save it securely.',
                'type': 'success',
                'sticky': True,
            }
        }

    def action_activate(self):
        """Activate the chatbot"""
        self.write({'status': 'active'})

    def action_deactivate(self):
        """Deactivate the chatbot"""
        self.write({'status': 'archived'})

    def sync_to_fastapi(self):
        """Sync chatbot configuration to FastAPI"""
        fastapi_url = self.env['ir.config_parameter'].sudo().get_param('fastapi.url', 'http://fastapi:8000')
        internal_key = self.env['ir.config_parameter'].sudo().get_param('fastapi.internal_key')
        
        if not internal_key:
            _logger.warning("FastAPI internal key not configured")
            return False
        
        payload = {
            'chatbot_id': self.id,
            'name': self.name,
            'status': self.status,
            'is_public': self.is_public,
            'allowed_domains': self.allowed_domains,
        }
        
        try:
            response = requests.post(
                f"{fastapi_url}/api/internal/chatbot/{self.id}/sync",
                json=payload,
                headers={'X-Odoo-API-Key': internal_key},
                timeout=30
            )
            
            if response.status_code == 200:
                _logger.info(f"Successfully synced chatbot {self.id} to FastAPI")
                return True
            else:
                _logger.error(f"Failed to sync chatbot {self.id}: {response.text}")
                return False
                
        except Exception as e:
            _logger.error(f"Error syncing chatbot {self.id}: {str(e)}")
            return False

    def unlink(self):
        """Override to cleanup FastAPI data before deletion"""
        fastapi_url = self.env['ir.config_parameter'].sudo().get_param('fastapi.url', 'http://fastapi:8000')
        internal_key = self.env['ir.config_parameter'].sudo().get_param('fastapi.internal_key')
        
        for chatbot in self:
            if internal_key:
                try:
                    response = requests.delete(
                        f"{fastapi_url}/api/internal/chatbot/{chatbot.id}/cleanup",
                        headers={'X-Odoo-API-Key': internal_key},
                        timeout=60
                    )
                    
                    if response.status_code != 200:
                        _logger.error(f"Failed to cleanup chatbot {chatbot.id}: {response.text}")
                except Exception as e:
                    _logger.error(f"Error cleaning up chatbot {chatbot.id}: {str(e)}")
        
        return super().unlink()

    @api.model
    def validate_api_key(self, chatbot_id, api_key):
        """Validate API key for external access"""
        if not api_key or not api_key.startswith('YOUR_API_KEY_HERE'):
            return False
        
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find chatbot with matching hash
        chatbot = self.search([
            ('id', '=', chatbot_id),
            ('api_key_hash', '=', key_hash),
            ('status', '=', 'active')
        ], limit=1)
        
        return bool(chatbot)
