# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=False, methods=['GET'])
def get_user_profile():
	"""
	Get comprehensive user profile information

	Returns:
		Dictionary with user profile details including subscription info
	"""
	try:
		user_email = frappe.session.user

		# Get User document
		user = frappe.get_doc('User', user_email)

		# Build profile data
		profile_data = {
			'email': user.email,
			'full_name': user.full_name or '',
			'first_name': user.first_name or '',
			'last_name': user.last_name or '',
			'username': user.username or user.email.split('@')[0],
			'mobile_no': user.mobile_no or '',
			'phone': user.phone or '',
			'location': user.location or '',
			'language': user.language or 'English',
			'time_zone': user.time_zone or '',
			'user_image': user.user_image or '',
			'creation': user.creation,
			'enabled': user.enabled,
			'user_type': user.user_type or 'Website User',
		}

		# Default subscription
		profile_data['subscription'] = {
			'type': '1 Day Trial',
			'status': 'Active',
			'start_date': None,
			'end_date': None,
		}

		# Get subscription information if table exists
		if frappe.db.exists('DocType', 'AI Subscription'):
			try:
				# Get active subscription with plan details
				subscription = frappe.db.sql("""
					SELECT
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

				# Add subscription data if available
				if subscription and len(subscription) > 0:
					sub = subscription[0]
					profile_data['subscription'] = {
						'type': sub.get('plan_name') or sub.get('plan_id') or '1 Day Trial',
						'status': sub.get('status', 'Active'),
						'start_date': sub.get('start_date'),
						'end_date': sub.get('end_date'),
					}
			except Exception as e:
				frappe.logger().error(f'Error fetching subscription: {str(e)}')
				# Continue with default subscription

		return {
			'success': True,
			'profile': profile_data
		}

	except Exception as e:
		frappe.logger().error(f'Error fetching user profile: {str(e)}')
		return {
			'success': False,
			'message': 'Error fetching user profile'
		}
