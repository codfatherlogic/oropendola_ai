# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime


class AISupportTicket(Document):
	def before_insert(self):
		"""Set created_date before inserting"""
		self.created_date = datetime.now()
		self.updated_date = datetime.now()

	def before_save(self):
		"""Update modified timestamp"""
		self.updated_date = datetime.now()

	def after_insert(self):
		"""Send confirmation and notification emails after creating ticket"""
		send_ticket_confirmation_email(self.name, self.user_email, self.user_name, self.subject)
		send_ticket_notification_to_support(self.name, self.user_email, self.subject, self.description, self.category)


def send_ticket_confirmation_email(ticket_id, user_email, user_name, subject):
	"""Send confirmation email to user"""
	try:
		email_body = f"""
		<html>
			<body style="font-family: Arial, sans-serif; color: #333;">
				<h2>Support Ticket Confirmation</h2>
				<p>Dear {user_name},</p>
				<p>Thank you for contacting Oropendola AI support. We have received your support request.</p>
				
				<div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
					<h3>Ticket Details</h3>
					<p><strong>Ticket ID:</strong> {ticket_id}</p>
					<p><strong>Subject:</strong> {subject}</p>
					<p><strong>Status:</strong> Open</p>
					<p><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
				</div>
				
				<p>Our support team will review your request and get back to you as soon as possible. You can track the status of your ticket using the Ticket ID above.</p>
				
				<p>If you need to provide additional information, please reply to this email with your Ticket ID.</p>
				
				<p>Best regards,<br>
				Oropendola AI Support Team</p>
				
				<hr>
				<p style="font-size: 12px; color: #666;">
					This is an automated message. Please do not reply directly to this email. Use your account dashboard to update your ticket.
				</p>
			</body>
		</html>
		"""
		
		frappe.sendmail(
			recipients=[user_email],
			sender="noreply@oropendola.ai",
			subject=f"[{ticket_id}] Support Ticket Confirmation - {subject}",
			message=email_body,
			now=True
		)
		frappe.logger().info(f'Confirmation email sent to {user_email} for ticket {ticket_id}')
	except Exception as e:
		frappe.logger().error(f'Failed to send confirmation email: {str(e)}')


def send_ticket_notification_to_support(ticket_id, user_email, subject, description, category):
	"""Send notification email to support team"""
	try:
		email_body = f"""
		<html>
			<body style="font-family: Arial, sans-serif; color: #333;">
				<h2>New Support Ticket Received</h2>
				
				<div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
					<h3>Ticket Information</h3>
					<p><strong>Ticket ID:</strong> {ticket_id}</p>
					<p><strong>User Email:</strong> {user_email}</p>
					<p><strong>Category:</strong> {category}</p>
					<p><strong>Subject:</strong> {subject}</p>
					<p><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
				</div>
				
				<h3>Description</h3>
				<div style="background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
					{description}
				</div>
				
				<p style="margin-top: 20px;">
					<a href="https://oropendola.ai/app/ai-support-ticket/{ticket_id}" 
					   style="background: #7B61FF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
						View Full Ticket
					</a>
				</p>
			</body>
		</html>
		"""
		
		frappe.sendmail(
			recipients=["hello@oropendola.ai"],
			sender="noreply@oropendola.ai",
			subject=f"[{ticket_id}] New Support Ticket - {category}: {subject}",
			message=email_body,
			now=True
		)
		frappe.logger().info(f'Notification email sent to support for ticket {ticket_id}')
	except Exception as e:
		frappe.logger().error(f'Failed to send support notification email: {str(e)}')