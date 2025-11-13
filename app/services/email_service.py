import resend
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configure Resend with API key
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Service for sending emails via Resend API"""
    
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email using Resend API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Send email via Resend
            params = {
                "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            email = resend.Emails.send(params)
            
            logger.info(f"Email sent successfully to {to_email} (ID: {email.get('id', 'N/A')})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_otp_email(to_email: str, otp_code: str) -> bool:
        """
        Send OTP verification email
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        current_year = datetime.now().year
        subject = f"Verify Your Email - {settings.APP_NAME}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4F46E5;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9fafb;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4F46E5;
                    text-align: center;
                    padding: 20px;
                    background-color: white;
                    border-radius: 5px;
                    letter-spacing: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{settings.APP_NAME}</h1>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Thank you for signing up! Please use the following OTP code to verify your email address:</p>
                    
                    <div class="otp-code">{otp_code}</div>
                    
                    <p>This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
                    
                    <p>If you didn't request this verification, please ignore this email.</p>
                    
                    <div class="footer">
                        <p>&copy; {current_year} {settings.APP_NAME}. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await EmailService.send_email(to_email, subject, html_content)
    
    @staticmethod
    async def send_welcome_email(to_email: str, organization_data: dict) -> bool:
        """
        Send welcome email after organization creation
        
        Args:
            to_email: Recipient email address
            organization_data: Dictionary with organization details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        company_name = organization_data.get('organization_name', 'Your Organization')
        org_code = organization_data.get('organization_code', 'N/A')
        industry = organization_data.get('industry', 'N/A')
        employees = organization_data.get('employees_count_range', 'N/A')
        country = organization_data.get('country', 'N/A')
        currency = organization_data.get('currency', 'N/A')
        plan = organization_data.get('plan', 'Free Trial')
        current_year = datetime.now().year
        subject = f"Welcome to {settings.APP_NAME}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4F46E5;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9fafb;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to {settings.APP_NAME}!</h1>
                </div>
                <div class="content">
                    <h2>Your Organization is Ready!</h2>
                    <p>Congratulations! Your organization <strong>{company_name}</strong> has been successfully created.</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #10b981;">📋 Organization Details</h3>
                        <div class="info-item">
                            <span class="info-label">Organization Name:</span>
                            <span class="info-value">{company_name}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Organization Code:</span>
                            <span class="info-value"><strong>{org_code}</strong></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Industry:</span>
                            <span class="info-value">{industry}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Employee Range:</span>
                            <span class="info-value">{employees}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Country:</span>
                            <span class="info-value">{country}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Currency:</span>
                            <span class="info-value">{currency}</span>
                        </div>
                        <div class="info-item" style="border-bottom: none;">
                            <span class="info-label">Plan:</span>
                            <span class="info-value"><strong style="color: #10b981;">{plan}</strong></span>
                        </div>
                    </div>
                    
                    <p>You can now start managing your team's attendance and enjoy all the features {settings.APP_NAME} has to offer.</p>
                    
                    <div style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}" class="button">Get Started</a>
                    </div>
                    
                    <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
                    
                    <div class="footer">
                        <p>&copy; {current_year} {settings.APP_NAME}. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await EmailService.send_email(to_email, subject, html_content)
    
    @staticmethod
    async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        current_year = datetime.now().year
        subject = f"Reset Your Password - {settings.APP_NAME}"
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1>🔐 {settings.APP_NAME}</h1></div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset your password. Click the button below:</p>
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    <p>Or copy this link: <br><small>{reset_link}</small></p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <div class="footer"><p>&copy; {current_year} {settings.APP_NAME}. All rights reserved.</p></div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await EmailService.send_email(to_email, subject, html_content)

    @staticmethod
    async def send_employee_access_email(
        to_email: str,
        full_name: str,
        organization_name: str,
        organization_code: str,
        employee_code: str,
        shift: str
    ) -> bool:
        """Send employee onboarding email with access credentials"""
        current_year = datetime.now().year
        subject = f"Welcome to {organization_name} on {settings.APP_NAME}!"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background-color: #f9fafb; border-radius: 8px; padding: 24px; margin-top: 16px; }}
                .code-box {{ background: #111827; color: #f9fafb; padding: 16px; border-radius: 6px; font-size: 20px; letter-spacing: 2px; text-align: center; margin: 16px 0; }}
                .cta {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; font-size: 14px; color: #6b7280; margin-top: 32px; }}
                .list {{ margin: 0; padding-left: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Hi {full_name},</h2>
                <p>Welcome to <strong>{organization_name}</strong> on <strong>{settings.APP_NAME}</strong>!</p>
                <p>Your mobile access credentials are ready. Use the details below to sign in to the Attendeely mobile app and start taking attendance.</p>

                <div class="card">
                    <h3>🔐 Access Credentials</h3>
                    <p><strong>Organization Code:</strong></p>
                    <div class="code-box">{organization_code}</div>
                    <p><strong>Your Employee Code:</strong></p>
                    <div class="code-box">{employee_code}</div>
                    <p><strong>Assigned Shift:</strong> {shift}</p>
                </div>

                <div class="card">
                    <h3>📱 Get Started</h3>
                    <ol class="list">
                        <li>Download the Attendeely mobile app from your app store.</li>
                        <li>Open the app and choose <strong>"Employee Login"</strong>.</li>
                        <li>Enter the organization code and employee code shown above.</li>
                        <li>Follow the on-screen steps to complete setup and start marking your attendance.</li>
                    </ol>
                </div>

                <p>If you run into any issues, reach out to your HR manager or administrator for assistance.</p>

                <p>We’re excited to have you onboard!</p>

                <a class="cta" href="{settings.FRONTEND_URL}">Visit the Web Portal</a>

                <div class="footer">
                    <p>&copy; {current_year} {settings.APP_NAME}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await EmailService.send_email(to_email, subject, html_content)
