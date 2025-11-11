import requests
import logging
from bs4 import BeautifulSoup
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ChatbotLink(models.Model):
    _name = 'chatbot.link'
    _description = 'Chatbot Link'
    _order = 'created_at desc'

    chatbot_id = fields.Many2one('chatbot.chatbot', 'Chatbot', required=True, ondelete='cascade')
    url = fields.Char('URL', required=True)
    title = fields.Char('Page Title')
    content = fields.Text('Scraped Content')
    
    # Processing status
    processed = fields.Boolean('Processed', default=False)
    vector_sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('error', 'Error')
    ], 'Sync Status', default='pending')
    
    # Timestamps
    created_at = fields.Datetime('Created At', default=fields.Datetime.now, readonly=True)
    updated_at = fields.Datetime('Updated At', default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        # Create link record
        link = super().create(vals)
        
        # Scrape content and sync to FastAPI
        if link.url:
            link._scrape_content()
            if link.content:
                link.sync_to_fastapi()
        
        return link

    def write(self, vals):
        # Check if URL changed
        url_changed = 'url' in vals
        
        vals['updated_at'] = fields.Datetime.now()
        result = super().write(vals)
        
        if url_changed:
            # Re-scrape content if URL changed
            self._scrape_content()
            if self.content:
                # Re-sync to FastAPI
                self.sync_to_fastapi()
        
        return result

    def _scrape_content(self):
        """Scrape content from URL"""
        if not self.url:
            return
        
        try:
            # Add protocol if missing
            url = self.url
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            if title:
                self.title = title.get_text().strip()
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            self.content = text
            _logger.info(f"Successfully scraped content from {url}")
            
        except Exception as e:
            _logger.error(f"Error scraping content from {self.url}: {str(e)}")
            self.content = ""

    def sync_to_fastapi(self):
        """Send link to FastAPI for embedding"""
        if not self.content:
            _logger.warning(f"No content to sync for link {self.id}")
            return False
        
        # Get FastAPI URL from environment variable first, then config parameter
        import os
        fastapi_url = os.getenv('FASTAPI_URL') or self.env['ir.config_parameter'].sudo().get_param('fastapi.url', 'http://localhost:8000')
        internal_key = self.env['ir.config_parameter'].sudo().get_param('fastapi.internal_key')
        
        if not internal_key:
            _logger.warning("FastAPI internal key not configured")
            return False
        
        payload = {
            'chatbot_id': self.chatbot_id.id,
            'url': self.url,
            'content': self.content,
            'metadata': {
                'title': self.title or '',
                'scraped_at': self.created_at.isoformat() if self.created_at else None
            }
        }
        
        try:
            self.write({'vector_sync_status': 'pending'})
            
            response = requests.post(
                f"{fastapi_url}/api/internal/link/{self.id}/embed",
                json=payload,
                headers={'X-Odoo-API-Key': internal_key},
                timeout=300
            )
            
            if response.status_code == 200:
                self.write({
                    'vector_sync_status': 'synced',
                    'processed': True
                })
                _logger.info(f"Successfully synced link {self.id} to FastAPI")
                return True
            else:
                self.write({'vector_sync_status': 'error'})
                _logger.error(f"Failed to sync link {self.id}: {response.text}")
                return False
                
        except Exception as e:
            self.write({'vector_sync_status': 'error'})
            _logger.error(f"Error syncing link {self.id}: {str(e)}")
            return False

    def action_retry_sync(self):
        """Manual retry sync action"""
        self.sync_to_fastapi()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_rescrape(self):
        """Re-scrape content from URL"""
        self._scrape_content()
        if self.content:
            self.sync_to_fastapi()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def unlink(self):
        """Override to delete from pgvector before Odoo deletion"""
        # Get FastAPI URL from environment variable first, then config parameter
        import os
        fastapi_url = os.getenv('FASTAPI_URL') or self.env['ir.config_parameter'].sudo().get_param('fastapi.url', 'http://localhost:8000')
        internal_key = self.env['ir.config_parameter'].sudo().get_param('fastapi.internal_key')
        
        for record in self:
            if record.processed and internal_key:
                try:
                    response = requests.delete(
                        f"{fastapi_url}/api/internal/chatbot/{record.chatbot_id.id}/source/link/{record.id}",
                        headers={'X-Odoo-API-Key': internal_key},
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        _logger.error(f"Failed to delete embeddings for link {record.id}: {response.text}")
                except Exception as e:
                    _logger.error(f"Error deleting embeddings for link {record.id}: {str(e)}")
        
        return super().unlink()
