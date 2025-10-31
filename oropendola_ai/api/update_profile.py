# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=False, methods=['POST'])
def update_full_name(full_name):
	"""
	Update user's full name

	Args:
		full_name: New full name

	Returns:
		Dictionary with success status
	"""
	try:
		user_email = frappe.session.user

		# Get User document
		user = frappe.get_doc('User', user_email)

		# Update full name
		name_parts = full_name.split(' ', 1)
		user.first_name = name_parts[0]
		user.last_name = name_parts[1] if len(name_parts) > 1 else ''
		user.full_name = full_name

		user.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			'success': True,
			'message': 'Full name updated successfully',
			'full_name': full_name
		}

	except Exception as e:
		frappe.logger().error(f'Error updating full name: {str(e)}')
		frappe.db.rollback()
		return {
			'success': False,
			'message': 'Failed to update full name'
		}
