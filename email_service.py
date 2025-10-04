# core/services/email_service.py
# Email Service Implementation

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Context, Template
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service for sending various types of emails
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com')
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', 'CRM System')
    
    def send_verification_email(self, user, verification_token):
        """
        Send email verification email
        """
        try:
            subject = "Verify Your Email Address"
            
            # Create verification URL
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Email Verification</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066CC;">Welcome to CRM System!</h2>
                    <p>Hello {user.first_name or user.email},</p>
                    <p>Thank you for registering with our CRM system. To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #0066CC; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #0066CC;">{verification_url}</p>
                    
                    <p>This verification link will expire in 24 hours.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        If you didn't create an account with us, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=f"{self.from_name} <{self.from_email}>",
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    def send_password_reset_email(self, user, reset_token):
        """
        Send password reset email
        """
        try:
            subject = "Reset Your Password"
            
            # Create reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Password Reset</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066CC;">Password Reset Request</h2>
                    <p>Hello {user.first_name or user.email},</p>
                    <p>We received a request to reset your password. Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #0066CC; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #0066CC;">{reset_url}</p>
                    
                    <p>This reset link will expire in 24 hours.</p>
                    <p>If you didn't request a password reset, please ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        For security reasons, this link will only work once.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=f"{self.from_name} <{self.from_email}>",
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False
    
    def send_welcome_email(self, user):
        """
        Send welcome email to new user
        """
        try:
            subject = "Welcome to CRM System!"
            
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066CC;">Welcome to CRM System!</h2>
                    <p>Hello {user.first_name or user.email},</p>
                    <p>Welcome to our CRM system! Your account has been successfully created and verified.</p>
                    
                    <h3>Getting Started:</h3>
                    <ul>
                        <li>Complete your profile information</li>
                        <li>Set up your preferences</li>
                        <li>Explore the dashboard</li>
                        <li>Start managing your contacts and deals</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/dashboard" 
                           style="background-color: #0066CC; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>
                    
                    <p>If you have any questions, please don't hesitate to contact our support team.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        Thank you for choosing our CRM system!
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=f"{self.from_name} <{self.from_email}>",
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    def send_notification_email(self, user, subject, message, action_url=None):
        """
        Send general notification email
        """
        try:
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Notification</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066CC;">{subject}</h2>
                    <p>Hello {user.first_name or user.email},</p>
                    <p>{message}</p>
                    
                    {f'''
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{action_url}" 
                           style="background-color: #0066CC; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            View Details
                        </a>
                    </div>
                    ''' if action_url else ''}
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated notification from CRM System.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=f"{self.from_name} <{self.from_email}>",
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Notification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification email to {user.email}: {str(e)}")
            return False
    
    def send_quote_email(self, quote, contact_email):
        """
        Send quote email to customer
        """
        try:
            subject = f"Quote #{quote.quote_number} - {quote.account.name}"
            
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Quote</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066CC;">Quote #{quote.quote_number}</h2>
                    <p>Dear {quote.account.name},</p>
                    <p>Thank you for your interest in our products/services. Please find attached your quote.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0;">
                        <h3>Quote Summary:</h3>
                        <p><strong>Quote Number:</strong> {quote.quote_number}</p>
                        <p><strong>Valid Until:</strong> {quote.valid_until or 'N/A'}</p>
                        <p><strong>Total Amount:</strong> {quote.currency} {quote.total_amount:,.2f}</p>
                    </div>
                    
                    <p>If you have any questions about this quote, please don't hesitate to contact us.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        This quote is valid until the specified date.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),
                from_email=f"{self.from_name} <{self.from_email}>",
                to=[contact_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Quote email sent to {contact_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send quote email to {contact_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
