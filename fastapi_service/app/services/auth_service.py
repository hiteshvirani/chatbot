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
                # Handle JSON-RPC format: {"jsonrpc": "2.0", "result": {"valid": true}}
                # or direct format: {"valid": true}
                if isinstance(result, dict):
                    if 'result' in result:
                        # JSON-RPC format
                        validation_result = result.get('result', {})
                        is_valid = validation_result.get('valid', False)
                    else:
                        # Direct format
                        is_valid = result.get('valid', False)
                    
                    if is_valid:
                        # Get chatbot info - Odoo JSON endpoint expects POST with JSON-RPC
                        info_response = await self.odoo_client.post(
                            f"{settings.odoo_url}/api/chatbot/{chatbot_id}/info",
                            json={},  # Empty JSON body for JSON-RPC
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if info_response.status_code == 200:
                            info_data = info_response.json()
                            # Handle JSON-RPC format for info endpoint
                            if isinstance(info_data, dict) and 'result' in info_data:
                                return info_data.get('result', {})
                            return info_data
            
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
