from odoo import models, fields, api


class ChatbotPrompt(models.Model):
    _name = 'chatbot.prompt'
    _description = 'Chatbot Prompt'
    _order = 'order, id'

    chatbot_id = fields.Many2one('chatbot.chatbot', 'Chatbot', required=True, ondelete='cascade')
    prompt_text = fields.Text('Prompt Text', required=True)
    prompt_type = fields.Selection([
        ('system', 'System Prompt'),
        ('user_template', 'User Template'),
    ], 'Prompt Type', required=True, default='system')
    order = fields.Integer('Order', default=10)
    is_active = fields.Boolean('Active', default=True)
    
    # Timestamps
    created_at = fields.Datetime('Created At', default=fields.Datetime.now, readonly=True)
