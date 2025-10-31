# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=False, methods=['GET'])
def get_billing_info():
	"""
	Get billing and subscription information for the current user

	Returns:
		Dictionary with subscription and billing history
	"""
	try:
		user_email = frappe.session.user

		# Default plan for users without subscription
		current_plan = {
			'plan_type': '1 Day Trial',
			'expires_on': None,
			'status': 'Active'
		}

		history = []

		# Check if AI Subscription doctype exists
		if frappe.db.exists('DocType', 'AI Subscription'):
			try:
				# Get current active subscription with plan details
				subscription = frappe.db.sql("""
					SELECT
						s.name,
						s.status,
						s.start_date,
						s.end_date,
						p.title as plan_name,
						p.plan_id
					FROM `tabAI Subscription` s
					LEFT JOIN `tabAI Plan` p ON s.plan = p.name
					WHERE s.user = %s
					AND s.status IN ('Active', 'Trial')
					ORDER BY s.creation DESC
					LIMIT 1
				""", (user_email,), as_dict=True)

				# Get plan details if subscription exists
				if subscription and len(subscription) > 0:
					sub = subscription[0]
					current_plan = {
						'plan_type': sub.get('plan_name') or sub.get('plan_id') or '1 Day Trial',
						'expires_on': sub.get('end_date'),
						'status': sub.get('status', 'Active')
					}

				# Get subscription history (billing transactions)
				history = frappe.db.sql("""
					SELECT
						s.name,
						s.status,
						s.start_date,
						s.end_date,
						s.creation,
						s.modified,
						p.title as plan_name,
						p.price
					FROM `tabAI Subscription` s
					LEFT JOIN `tabAI Plan` p ON s.plan = p.name
					WHERE s.user = %s
					ORDER BY s.creation DESC
					LIMIT 10
				""", (user_email,), as_dict=True)
			except Exception as e:
				frappe.logger().error(f'Error querying AI Subscription: {str(e)}')
				# Continue with default values

		return {
			'success': True,
			'current_plan': current_plan,
			'history': history
		}

	except Exception as e:
		frappe.logger().error(f'Error fetching billing info: {str(e)}')
		# Return default data instead of error
		return {
			'success': True,
			'current_plan': {
				'plan_type': '1 Day Trial',
				'expires_on': None,
				'status': 'Active'
			},
			'history': []
		}
