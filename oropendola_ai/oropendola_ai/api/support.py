# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Support and Enterprise Inquiry API
Handles support tickets and enterprise contact form submissions
"""

import frappe
from frappe import _
import json


@frappe.whitelist(allow_guest=True)
def submit_enterprise_inquiry(
    full_name: str,
    email: str,
    phone: str,
    company: str,
    job_title: str,
    num_accounts: str,
    message: str = ""
):
    """
    Submit enterprise inquiry form

    Args:
        full_name: Contact person's full name
        email: Work email address
        phone: Contact number
        company: Company name
        job_title: Job title
        num_accounts: Number of accounts needed
        message: Additional requirements (optional)

    Returns:
        dict: Success message with ticket ID
    """
    try:
        # Validate required fields
        if not all([full_name, email, phone, company, job_title, num_accounts]):
            return {
                "success": False,
                "error": "All required fields must be filled"
            }

        # Validate email format
        if "@" not in email or "." not in email:
            return {
                "success": False,
                "error": "Invalid email address"
            }

        # Create support ticket for enterprise inquiry
        ticket_subject = f"Enterprise Inquiry - {company}"

        ticket_description = f"""
<strong>Enterprise Plan Inquiry</strong>

<strong>Contact Information:</strong>
- Name: {full_name}
- Email: {email}
- Phone: {phone}
- Company: {company}
- Job Title: {job_title}

<strong>Requirements:</strong>
- Number of Accounts: {num_accounts}

<strong>Additional Information:</strong>
{message if message else 'No additional information provided'}

---
This inquiry was submitted via the Enterprise Contact Form.
Please respond within 24 hours.
"""

        # Create support ticket
        ticket = frappe.get_doc({
            "doctype": "Support Ticket",
            "subject": ticket_subject,
            "description": ticket_description,
            "contact_name": full_name,
            "contact_email": email,
            "contact_phone": phone,
            "priority": "High",  # Enterprise inquiries are high priority
            "ticket_type": "Enterprise Inquiry",
            "status": "Open"
        })

        ticket.insert(ignore_permissions=True)
        frappe.db.commit()

        # Send notification email to support team
        try:
            send_enterprise_inquiry_notification(ticket, {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "company": company,
                "job_title": job_title,
                "num_accounts": num_accounts,
                "message": message
            })
        except Exception as e:
            frappe.log_error(f"Failed to send enterprise inquiry notification: {str(e)}", "Enterprise Inquiry Notification Error")

        # Send confirmation email to customer
        try:
            send_enterprise_inquiry_confirmation(email, full_name, ticket.name)
        except Exception as e:
            frappe.log_error(f"Failed to send enterprise inquiry confirmation: {str(e)}", "Enterprise Inquiry Confirmation Error")

        return {
            "success": True,
            "ticket_id": ticket.name,
            "message": "Thank you for your interest in Oropendola AI Enterprise. Our team will contact you within 24 hours."
        }

    except Exception as e:
        frappe.log_error(f"Enterprise inquiry submission error: {str(e)}", "Enterprise Inquiry Error")
        return {
            "success": False,
            "error": f"Failed to submit inquiry: {str(e)}"
        }


def send_enterprise_inquiry_notification(ticket, inquiry_data):
    """
    Send email notification to support team about new enterprise inquiry

    Args:
        ticket: Support Ticket document
        inquiry_data: Dictionary with inquiry details
    """
    try:
        # Get support email from settings
        support_email = frappe.db.get_single_value("Oropendola Settings", "support_ticket_receiver_email")

        if not support_email:
            support_email = "support@oropendola.ai"  # Fallback

        subject = f"🎯 New Enterprise Inquiry - {inquiry_data['company']}"

        message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #7B61FF 0%, #00D9FF 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">New Enterprise Inquiry</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Ticket #{ticket.name}</p>
    </div>

    <div style="background: #f9f9f9; padding: 30px;">
        <h2 style="color: #333; border-bottom: 2px solid #7B61FF; padding-bottom: 10px;">Contact Details</h2>
        <table style="width: 100%; margin: 20px 0;">
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Name:</strong></td>
                <td style="padding: 10px 0; color: #333;">{inquiry_data['full_name']}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Email:</strong></td>
                <td style="padding: 10px 0; color: #333;"><a href="mailto:{inquiry_data['email']}">{inquiry_data['email']}</a></td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Phone:</strong></td>
                <td style="padding: 10px 0; color: #333;"><a href="tel:{inquiry_data['phone']}">{inquiry_data['phone']}</a></td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Company:</strong></td>
                <td style="padding: 10px 0; color: #333;">{inquiry_data['company']}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Job Title:</strong></td>
                <td style="padding: 10px 0; color: #333;">{inquiry_data['job_title']}</td>
            </tr>
        </table>

        <h2 style="color: #333; border-bottom: 2px solid #7B61FF; padding-bottom: 10px; margin-top: 30px;">Requirements</h2>
        <table style="width: 100%; margin: 20px 0;">
            <tr>
                <td style="padding: 10px 0; color: #666;"><strong>Number of Accounts:</strong></td>
                <td style="padding: 10px 0; color: #333;">{inquiry_data['num_accounts']}</td>
            </tr>
        </table>

        {f'''
        <h2 style="color: #333; border-bottom: 2px solid #7B61FF; padding-bottom: 10px; margin-top: 30px;">Additional Information</h2>
        <div style="background: white; padding: 20px; border-left: 4px solid #7B61FF; margin: 20px 0;">
            <p style="color: #333; line-height: 1.6; margin: 0;">{inquiry_data['message']}</p>
        </div>
        ''' if inquiry_data.get('message') else ''}

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 30px 0;">
            <p style="color: #856404; margin: 0;"><strong>⏰ Response Required:</strong> Please respond within 24 hours.</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{frappe.utils.get_url()}/app/support-ticket/{ticket.name}"
               style="display: inline-block; background: linear-gradient(135deg, #7B61FF 0%, #00D9FF 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                View Ticket
            </a>
        </div>
    </div>

    <div style="background: #333; padding: 20px; text-align: center;">
        <p style="color: #999; margin: 0; font-size: 12px;">© 2025 Oropendola AI. All rights reserved.</p>
    </div>
</div>
"""

        frappe.sendmail(
            recipients=[support_email],
            subject=subject,
            message=message,
            now=True
        )

    except Exception as e:
        frappe.log_error(f"Failed to send enterprise inquiry notification: {str(e)}", "Enterprise Notification Error")


def send_enterprise_inquiry_confirmation(email, name, ticket_id):
    """
    Send confirmation email to customer

    Args:
        email: Customer email
        name: Customer name
        ticket_id: Support ticket ID
    """
    try:
        subject = "Thank you for your Enterprise inquiry - Oropendola AI"

        message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #7B61FF 0%, #00D9FF 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">Thank You!</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">We've received your Enterprise inquiry</p>
    </div>

    <div style="background: #f9f9f9; padding: 30px;">
        <p style="color: #333; font-size: 16px;">Dear {name},</p>

        <p style="color: #333; line-height: 1.6;">
            Thank you for your interest in <strong>Oropendola AI Enterprise</strong>. We're excited to help transform your organization's development workflow.
        </p>

        <div style="background: white; border: 2px solid #7B61FF; border-radius: 8px; padding: 20px; margin: 30px 0;">
            <h2 style="color: #7B61FF; margin: 0 0 15px 0; font-size: 18px;">What happens next?</h2>
            <ul style="color: #333; line-height: 1.8; margin: 0; padding-left: 20px;">
                <li>Our enterprise team will review your requirements</li>
                <li>We'll contact you within <strong>24 hours</strong></li>
                <li>Schedule a personalized demo and discovery call</li>
                <li>Receive a custom proposal tailored to your needs</li>
            </ul>
        </div>

        <div style="background: #e8f4fd; border-left: 4px solid #00D9FF; padding: 20px; margin: 30px 0;">
            <p style="color: #333; margin: 0;">
                <strong>Your Ticket ID:</strong> <code style="background: white; padding: 4px 8px; border-radius: 4px;">{ticket_id}</code>
            </p>
            <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">
                Save this ID for future reference.
            </p>
        </div>

        <p style="color: #333; line-height: 1.6;">
            If you have any immediate questions, feel free to reply to this email or contact us at:
        </p>

        <div style="text-align: center; margin: 20px 0;">
            <p style="color: #333; margin: 5px 0;">📧 <a href="mailto:support@oropendola.ai" style="color: #7B61FF;">support@oropendola.ai</a></p>
        </div>

        <p style="color: #333; line-height: 1.6; margin-top: 30px;">
            Best regards,<br>
            <strong>Oropendola AI Enterprise Team</strong>
        </p>
    </div>

    <div style="background: #333; padding: 20px; text-align: center;">
        <p style="color: #999; margin: 0; font-size: 12px;">© 2025 Oropendola AI. All rights reserved.</p>
        <p style="color: #666; margin: 10px 0 0 0; font-size: 12px;">
            <a href="{frappe.utils.get_url()}" style="color: #00D9FF; text-decoration: none;">Visit our website</a>
        </p>
    </div>
</div>
"""

        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message,
            now=True
        )

    except Exception as e:
        frappe.log_error(f"Failed to send enterprise inquiry confirmation: {str(e)}", "Enterprise Confirmation Error")


@frappe.whitelist(allow_guest=True)
def submit_support_ticket(
    name: str,
    email: str,
    subject: str,
    message: str,
    phone: str = ""
):
    """
    Submit general support ticket

    Args:
        name: Customer name
        email: Email address
        subject: Ticket subject
        message: Ticket message/description
        phone: Phone number (optional)

    Returns:
        dict: Success message with ticket ID
    """
    try:
        # Validate required fields
        if not all([name, email, subject, message]):
            return {
                "success": False,
                "error": "All required fields must be filled"
            }

        # Validate email format
        if "@" not in email or "." not in email:
            return {
                "success": False,
                "error": "Invalid email address"
            }

        # Create support ticket
        ticket = frappe.get_doc({
            "doctype": "Support Ticket",
            "subject": subject,
            "description": message,
            "contact_name": name,
            "contact_email": email,
            "contact_phone": phone or "",
            "priority": "Medium",
            "ticket_type": "General Support",
            "status": "Open"
        })

        ticket.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "ticket_id": ticket.name,
            "message": "Support ticket created successfully. We'll get back to you soon."
        }

    except Exception as e:
        frappe.log_error(f"Support ticket submission error: {str(e)}", "Support Ticket Error")
        return {
            "success": False,
            "error": f"Failed to submit ticket: {str(e)}"
        }
