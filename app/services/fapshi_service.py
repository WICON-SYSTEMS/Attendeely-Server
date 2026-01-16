"""
Fapshi Payment Service
Handles payment initiation and webhook processing via Fapshi API
"""
import requests
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fapshi API endpoints
FAPSHI_SANDBOX_URL = "https://sandbox.fapshi.com"
FAPSHI_PRODUCTION_URL = "https://fapshi.com"
FAPSHI_DIRECT_PAY_ENDPOINT = "/direct-pay"


class FapshiService:
    """Service for handling Fapshi payment operations"""
    
    @staticmethod
    def _get_base_url() -> str:
        """Get Fapshi base URL based on environment"""
        # Use sandbox for development, production for production
        # You can add an environment variable to control this
        if not settings.API_USER or not settings.API_KEY:
            logger.warning("Fapshi credentials not configured, using sandbox")
        # For now, default to sandbox. Add FAPSHI_ENV setting if needed
        return FAPSHI_SANDBOX_URL
    
    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Get Fapshi API headers"""
        if not settings.API_USER or not settings.API_KEY:
            raise ValueError("Fapshi API credentials not configured. Please set API_USER and API_KEY in environment variables.")
        
        return {
            "apiuser": settings.API_USER,
            "apikey": settings.API_KEY,
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def initiate_payment(
        amount: int,
        phone: str,
        email: str,
        name: str,
        external_id: str,
        medium: str = "mobile money",
        message: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a payment via Fapshi direct-pay
        
        Args:
            amount: Payment amount in base currency unit (e.g., XAF, not cents)
            phone: Customer phone number
            email: Customer email
            name: Customer name
            external_id: Your internal reference ID (e.g., subscription_id)
            medium: Payment medium (default: "mobile money")
            message: Optional payment message
            user_id: Optional user ID
            
        Returns:
            Dict with payment response:
            - On success: {"message": str, "transId": str, "dateInitiated": str}
            - On error: {"message": str}
        """
        try:
            base_url = FapshiService._get_base_url()
            url = f"{base_url}{FAPSHI_DIRECT_PAY_ENDPOINT}"
            headers = FapshiService._get_headers()
            
            payload = {
                "amount": amount,
                "phone": phone,
                "medium": medium,
                "name": name,
                "email": email,
                "externalId": external_id,
            }
            
            if message:
                payload["message"] = message
            
            if user_id:
                payload["userId"] = user_id
            
            logger.info(f"Initiating Fapshi payment: external_id={external_id}, amount={amount}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Log successful payment initiation
            if "transId" in result:
                logger.info(f"Fapshi payment initiated successfully: transId={result.get('transId')}, external_id={external_id}")
            else:
                logger.warning(f"Fapshi payment response missing transId: {result}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Fapshi API HTTP error: {str(e)}"
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    error_msg = f"{error_msg} - Status: {e.response.status_code}"
            
            logger.error(f"{error_msg} - external_id={external_id}")
            return {"message": error_msg}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Fapshi API request error: {str(e)}"
            logger.error(f"{error_msg} - external_id={external_id}")
            return {"message": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error initiating Fapshi payment: {str(e)}"
            logger.error(f"{error_msg} - external_id={external_id}")
            return {"message": error_msg}
    
    @staticmethod
    def verify_payment(trans_id: str) -> Dict[str, Any]:
        """
        Verify payment status via Fapshi API
        Note: This is a placeholder. Implement based on Fapshi's verification endpoint
        
        Args:
            trans_id: Fapshi transaction ID
            
        Returns:
            Dict with payment verification response
        """
        # TODO: Implement payment verification endpoint when available
        # This would typically be used in webhook verification
        logger.warning("Payment verification not yet implemented")
        return {"message": "Payment verification not yet implemented"}
