"""
Email Tracking Endpoints
Handles open tracking, click tracking, and unsubscribe requests
"""
from fastapi import APIRouter, Depends, Query, Response, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from urllib.parse import unquote, urlparse
import logging
from io import BytesIO

from app.core.database import get_db
from app.core.url_validator import URLValidator, URLSecurityError, validate_email_tracking_redirect
from app.core.rate_limiter import tracking_public_limiter, tracking_unsubscribe_limiter
from app.services.email_service import EmailService
from app.models import Lead

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/open/{tracking_token}")
@tracking_public_limiter
async def track_email_open(
    request: Request,
    tracking_token: str,
    db: Session = Depends(get_db)
):
    """
    Track email open event

    Returns a 1x1 transparent GIF pixel
    This endpoint is called when the tracking pixel loads in the email client
    """
    try:
        email_service = EmailService(db=db)
        pixel_bytes = email_service.track_open(tracking_token)

        return Response(
            content=pixel_bytes,
            media_type="image/gif",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except Exception as e:
        logger.error(f"Error tracking email open: {str(e)}")
        # Still return pixel even if tracking fails
        # Don't break the email experience
        pixel_bytes = bytes.fromhex(
            '474946383961010001008000000000000021f90401000000002c00000000'
            '010001000002024401003b'
        )
        return Response(content=pixel_bytes, media_type="image/gif")


@router.get("/click/{tracking_token}")
@tracking_public_limiter
async def track_email_click(
    request: Request,
    tracking_token: str,
    url: str = Query(..., description="Original URL to redirect to"),
    db: Session = Depends(get_db)
):
    """
    Track email click event and redirect to original URL

    SECURITY: Validates redirect URL to prevent open redirect attacks
    OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html

    Args:
        tracking_token: Unique tracking token
        url: Original URL to redirect to (URL-encoded)

    Returns:
        Redirect to validated URL
    """
    try:
        # Decode URL
        original_url = unquote(url)

        # Validate redirect URL to prevent open redirect attacks
        from app.core.security_config import get_email_redirect_allowed_domains

        try:
            # Validate the redirect URL using centralized config
            validated_url = validate_email_tracking_redirect(
                original_url,
                get_email_redirect_allowed_domains()
            )
        except URLSecurityError as e:
            logger.warning(f"Blocked suspicious redirect URL: {original_url} - {e}")
            # Return to a safe default page instead of the suspicious URL
            raise HTTPException(
                status_code=400,
                detail="Invalid redirect URL. For security reasons, we cannot redirect to this URL."
            )

        # Track click
        email_service = EmailService(db=db)
        # Use the validated URL for tracking
        redirect_url = email_service.track_click(tracking_token, validated_url)

        # Ensure the returned URL is also validated (defense in depth)
        try:
            final_url = validate_email_tracking_redirect(
                redirect_url,
                get_email_redirect_allowed_domains()
            )
        except URLSecurityError:
            # If the service returns an invalid URL, use the validated original
            final_url = validated_url

        # Redirect to validated URL
        return RedirectResponse(
            url=final_url,
            status_code=302
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error tracking email click: {str(e)}")
        # Don't redirect to unvalidated URL even if tracking fails
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request."
        )


@router.get("/unsubscribe/{tracking_token}")
@tracking_unsubscribe_limiter
async def unsubscribe_from_emails(
    request: Request,
    tracking_token: str,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe lead from email campaigns

    Args:
        tracking_token: Unique tracking token

    Returns:
        HTML confirmation page
    """
    try:
        email_service = EmailService(db=db)

        # Decode tracking token
        campaign_id, lead_id = email_service._decode_tracking_token(tracking_token)

        # Update lead to mark as unsubscribed
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Set lead status or add unsubscribe flag
        # Assuming we have an 'email_unsubscribed' field in Lead model
        # If not, we'll need to add it or use status
        if hasattr(lead, 'email_unsubscribed'):
            lead.email_unsubscribed = True
        else:
            # Fallback: mark as opted_out
            lead.status = 'opted_out'

        db.commit()

        logger.info(f"Lead unsubscribed: lead_id={lead_id}, email={lead.email}")

        # Return confirmation HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Unsubscribed - FlipTech Pro</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 40px 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 500px;
                    text-align: center;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 15px;
                }}
                .email {{
                    font-weight: bold;
                    color: #007bff;
                }}
                .success-icon {{
                    font-size: 48px;
                    color: #28a745;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>You've Been Unsubscribed</h1>
                <p>
                    The email address <span class="email">{lead.email}</span>
                    has been successfully removed from our mailing list.
                </p>
                <p>
                    You will no longer receive marketing emails from FlipTech Pro.
                </p>
                <p style="margin-top: 30px; font-size: 14px; color: #999;">
                    If this was a mistake, please contact us at support@fliptechpro.com
                </p>
            </div>
        </body>
        </html>
        """

        return Response(content=html_content, media_type="text/html")

    except ValueError as e:
        logger.error(f"Invalid tracking token: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid tracking token")

    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")


@router.get("/unsubscribe-confirm")
@tracking_unsubscribe_limiter
async def unsubscribe_confirmation(request: Request):
    """
    Generic unsubscribe confirmation page
    Used if direct token unsubscribe fails
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Unsubscribe - FlipTech Pro</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 40px 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 500px;
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            p {
                color: #666;
                line-height: 1.6;
                margin-bottom: 15px;
            }
            input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-bottom: 15px;
                font-size: 16px;
            }
            button {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unsubscribe from Emails</h1>
            <p>
                Enter your email address below to unsubscribe from our mailing list.
            </p>
            <form action="/api/v1/tracking/unsubscribe-submit" method="post">
                <input type="email" name="email" placeholder="your@email.com" required>
                <button type="submit">Unsubscribe</button>
            </form>
            <p style="margin-top: 30px; font-size: 14px; color: #999;">
                Contact us at support@fliptechpro.com if you need assistance
            </p>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


# TODO: Add endpoint for manual unsubscribe by email
# @router.post("/unsubscribe-submit")
# async def unsubscribe_by_email(
#     email: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     Unsubscribe lead by email address
#     Used by the manual unsubscribe form
#     """
#     pass
