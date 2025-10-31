# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=False, methods=['GET', 'POST'])
def create_support_ticket(user_name, subject, description, category, priority="Medium"):
	"""
	Create a new support ticket

	Args:
		user_name: User's full name
		subject: Ticket subject
		description: Detailed description
		category: Issue category
		priority: Priority level (Low, Medium, High, Critical)

	Returns:
		Dictionary with success status and ticket details
	"""
	try:
		# Get current user's email
		user_email = frappe.session.user
		
		# Validate inputs
		if not all([user_name, subject, description, category]):
			return {
				'success': False,
				'message': 'Missing required fields'
			}
		
		# Validate priority
		if priority not in ['Low', 'Medium', 'High', 'Critical']:
			priority = 'Medium'
		
		# Validate category
		valid_categories = [
			'General Inquiry',
			'Technical Support',
			'Billing & Payments',
			'Feature Request',
			'Bug Report',
			'API Integration',
			'Enterprise Solutions',
			'Partnership',
			'Account Issues',
			'Other'
		]
		
		if category not in valid_categories:
			return {
				'success': False,
				'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
			}
		
		# Create new support ticket
		ticket = frappe.get_doc({
			'doctype': 'AI Support Ticket',
			'user_email': user_email,
			'user_name': user_name,
			'subject': subject,
			'description': description,
			'category': category,
			'priority': priority,
			'status': 'Open'
		})
		
		ticket.insert(ignore_permissions=False)
		frappe.db.commit()
		
		frappe.logger().info(f'Support ticket created: {ticket.name} by user {user_email}')
		
		return {
			'success': True,
			'message': 'Support ticket created successfully',
			'ticket_id': ticket.name,
			'ticket_url': f'/app/ai-support-ticket/{ticket.name}'
		}
	
	except frappe.ValidationError as e:
		frappe.logger().error(f'Validation error creating support ticket: {str(e)}')
		return {
			'success': False,
			'message': str(e)
		}
	except Exception as e:
		frappe.logger().error(f'Error creating support ticket: {str(e)}')
		return {
			'success': False,
			'message': 'Error creating support ticket. Please try again.'
		}


@frappe.whitelist(allow_guest=False, methods=['GET', 'POST'])
def get_user_tickets():
	"""
	Get all support tickets for the current user
	
	Returns:
		List of tickets with key information
	"""
	try:
		user_email = frappe.session.user
		
		tickets = frappe.db.get_list(
			'AI Support Ticket',
			filters={'user_email': user_email},
			fields=['name', 'subject', 'category', 'priority', 'status', 'creation', 'modified', 'description'],
			order_by='creation desc'
		)
		
		return {
			'success': True,
			'tickets': tickets,
			'count': len(tickets)
		}
	
	except Exception as e:
		frappe.logger().error(f'Error fetching user tickets: {str(e)}')
		return {
			'success': False,
			'message': 'Error fetching tickets',
			'tickets': []
		}


@frappe.whitelist(allow_guest=False)
def get_ticket_details(ticket_id):
	"""
	Get detailed information about a specific ticket
	
	Args:
		ticket_id: Ticket ID to fetch
	
	Returns:
		Complete ticket details
	"""
	try:
		user_email = frappe.session.user
		
		# Verify user owns this ticket
		ticket = frappe.get_doc('AI Support Ticket', ticket_id)
		
		if ticket.user_email != user_email:
			return {
				'success': False,
				'message': 'Unauthorized access to this ticket'
			}
		
		return {
			'success': True,
			'ticket': {
				'ticket_id': ticket.name,
				'user_email': ticket.user_email,
				'user_name': ticket.user_name,
				'subject': ticket.subject,
				'description': ticket.description,
				'category': ticket.category,
				'priority': ticket.priority,
				'status': ticket.status,
				'created_date': ticket.created_date,
				'updated_date': ticket.updated_date,
				'resolution_notes': ticket.resolution_notes or ''
			}
		}
	
	except frappe.DoesNotExistError:
		return {
			'success': False,
			'message': 'Ticket not found'
		}
	except Exception as e:
		frappe.logger().error(f'Error fetching ticket details: {str(e)}')
		return {
			'success': False,
			'message': 'Error fetching ticket details'
		}
