from fastapi import APIRouter, status

from app.schemas.contact import ContactSupportRequest
from app.schemas.response import error_response, success_response
from app.services.email_service import EmailService

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/contact", status_code=status.HTTP_200_OK)
async def contact_support(payload: ContactSupportRequest):
    """
    Public endpoint for sending a support/contact message to Attendeely.
    """
    try:
        sent = await EmailService.send_support_contact_email(
            name=payload.name,
            from_email=payload.email,
            subject=payload.subject,
            message=payload.message,
        )

        if not sent:
            return error_response(
                message="Unable to send your message right now. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(
            message="Your message has been sent to Attendeely support.",
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return error_response(
            message="An unexpected error occurred while sending your message.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


