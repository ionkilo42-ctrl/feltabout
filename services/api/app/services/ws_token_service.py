"""
WebSocket access token service.

Provides scoped, time-limited tokens for WebSocket access.
Used when a user joins a conversation via invite link.

The token encodes:
- participant_id: who is joining
- space_id: which conversation space
- session_id: which backend session
- exp: expiration time (5 minutes default)

The backend/main.py WebSocket validates this token before allowing connection.
"""

import os
import time
import logging
from typing import Optional
import base64
import json

logger = logging.getLogger(__name__)

# Shared secret for signing WS tokens
# Both services/api and backend/main.py need to use the same key
def _get_ws_secret() -> bytes:
    secret = os.environ.get("WS_SHARED_SECRET")
    if not secret:
        env = os.environ.get("ENV", "development")
        if env == "production":
            raise RuntimeError(
                "WS_SHARED_SECRET environment variable is required in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        else:
            logger.warning(
                "⚠️  WARNING: WS_SHARED_SECRET not set. Using temporary key for development."
            )
            # Use the ENCRYPTION_KEY as fallback for dev, or generate temp
            enc_key = os.environ.get("ENCRYPTION_KEY")
            if enc_key:
                return enc_key.encode()[:32].ljust(32, b'0')
            return os.urandom(32)
    return secret.encode()


class WSTokenService:
    """Generate and validate scoped WebSocket access tokens."""
    
    def __init__(self):
        self.secret = _get_ws_secret()
    
    def create_token(
        self,
        participant_id: str,
        space_id: str,
        session_id: str,
        ttl_seconds: int = 300,  # 5 minutes
    ) -> str:
        """
        Create a scoped WS access token.
        
        The token is a simple signed payload: base64(json(payload))
        Signed with HMAC-SHA256 using the shared secret.
        
        Payload contains: participant_id, space_id, session_id, exp (unix timestamp)
        """
        payload = {
            "pid": participant_id,
            "sid": space_id,
            "wsid": session_id,
            "exp": int(time.time()) + ttl_seconds,
        }
        
        # JSON encode payload
        json_bytes = json.dumps(payload, separators=(',', ':')).encode()
        
        # Base64 encode (URL-safe)
        encoded_payload = base64.urlsafe_b64encode(json_bytes).decode()
        
        # Create HMAC signature
        import hmac
        signature = hmac.new(self.secret, encoded_payload.encode(), 'sha256').digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        # Token format: payload.signature
        token = f"{encoded_payload}.{signature_b64}"
        
        logger.debug(f"Created WS token for participant {participant_id}")
        return token
    
    def validate_token(
        self,
        token: str,
        expected_session_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Validate a WS access token.
        
        Returns payload dict if valid, None if:
        - Token is malformed
        - Signature doesn't match
        - Token is expired
        
        If expected_session_id provided, also validates the session_id matches.
        """
        try:
            parts = token.split('.')
            if len(parts) != 2:
                return None
            
            payload_b64, signature_b64 = parts
            
            # Verify signature
            import hmac
            expected_sig = hmac.new(
                self.secret, 
                payload_b64.encode(), 
                'sha256'
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
            
            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                logger.warning("WS token signature mismatch")
                return None
            
            # Decode payload
            json_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(json_bytes)
            
            # Check expiration
            exp = payload.get('exp', 0)
            if time.time() > exp:
                logger.warning(f"WS token expired (exp: {exp})")
                return None
            
            # Optional: validate session_id matches
            if expected_session_id and payload.get('wsid') != expected_session_id:
                logger.warning(f"WS token session mismatch: expected {expected_session_id}")
                return None
            
            return {
                "participant_id": payload['pid'],
                "space_id": payload['sid'],
                "session_id": payload['wsid'],
                "expires_at": exp,
            }
            
        except Exception as e:
            logger.warning(f"WS token validation error: {e}")
            return None


# Singleton instance
_ws_token_service: WSTokenService | None = None


def get_ws_token_service() -> WSTokenService:
    """Get or create the singleton WS token service."""
    global _ws_token_service
    if _ws_token_service is None:
        _ws_token_service = WSTokenService()
    return _ws_token_service