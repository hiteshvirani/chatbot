import hashlib
import logging
import httpx
from typing import Optional, Dict, Any
from app.config import settings

_logger = logging.getLogger(__name__)


class AuthService:
    
    def __init__(self):
        self.odoo_client = httpx.AsyncClient(timeout=30.0)

    async def validate_api_key(self, chatbot_id: int, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key with Odoo"""
        if not api_key or not api_key.startswith('YOUR_API_KEY_HERE'):
            return None

        try:
            # Call Odoo API to validate
            response = await self.odoo_client.post(
                f"{settings.odoo_url}/api/chatbot/validate",
                json={
                    'chatbot_id': chatbot_id,
                    'api_key': api_key
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('valid'):
                    # Get chatbot info
                    info_response = await self.odoo_client.get(
                        f"{settings.odoo_url}/api/chatbot/{chatbot_id}/info",
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if info_response.status_code == 200:
                        return info_response.json()
            
            return None
            
        except Exception as e:
            _logger.error(f"Error validating API key: {str(e)}")
            return None

    def validate_internal_api_key(self, api_key: str) -> bool:
        """Validate internal API key for Odoo → FastAPI communication"""
        return api_key == settings.internal_api_key

    def validate_domain(self, chatbot_info: Dict[str, Any], origin: str, referer: str) -> bool:
        """Validate if request origin is allowed"""
        allowed_domains = chatbot_info.get('allowed_domains')
        
        if not allowed_domains:
            return True  # No restrictions
        
        domains = [d.strip() for d in allowed_domains.split(',') if d.strip()]
        
        for domain in domains:
            if domain in origin or domain in referer:
                return True
        
        return False

    async def close(self):
        """Close HTTP client"""
        await self.odoo_client.aclose()


# Global instance
auth_service = AuthService()
