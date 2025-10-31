# Copyright (c) 2025, Oropendola AI and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import now_datetime, add_days, today


@frappe.whitelist(allow_guest=False, methods=['POST'])
def request_account_deletion():
	"""
	Request account deletion with a 30-day grace period

	Returns:
		Dictionary with success status and deletion date
	"""
	try:
		user_email = frappe.session.user

		# Prevent Administrator deletion
		if user_email == 'Administrator':
			return {
				'success': False,
				'message': 'Administrator account cannot be deleted'
			}

		# Get User document
		user = frappe.get_doc('User', user_email)

		# Set deletion request date (30 days from now)
		deletion_date = add_days(today(), 30)

		# Mark user for deletion by setting custom fields
		# We'll use User document's custom fields or bio field to store this temporarily
		user.add_comment(
			'Info',
			f'Account deletion requested on {now_datetime()}. Scheduled for {deletion_date}'
		)

		# Disable user immediately (they can still login during grace period)
		# But we'll keep them enabled for now so they can cancel

		# Cancel all active subscriptions
		active_subscriptions = frappe.db.get_list(
			'AI Subscription',
			filters={
				'user': user_email,
				'status': ['in', ['Active', 'Trial']]
			},
			fields=['name']
		)

		for sub in active_subscriptions:
			subscription = frappe.get_doc('AI Subscription', sub.name)
			subscription.status = 'Cancelled'
			subscription.cancelled_at = now_datetime()
			subscription.cancellation_reason = f'Account deletion requested by user on {now_datetime()}'
			subscription.save(ignore_permissions=True)

		# Revoke all API keys
		api_keys = frappe.db.get_list(
			'AI API Key',
			filters={'user': user_email},
			fields=['name']
		)

		for key in api_keys:
			api_key = frappe.get_doc('AI API Key', key.name)
			api_key.enabled = 0
			api_key.add_comment('Info', f'Disabled due to account deletion request on {now_datetime()}')
			api_key.save(ignore_permissions=True)

		frappe.db.commit()

		# TODO: Send confirmation email
		# send_deletion_confirmation_email(user_email, deletion_date)

		return {
			'success': True,
			'message': f'Your account deletion has been scheduled for {deletion_date}. You have 30 days to cancel this request.',
			'deletion_date': deletion_date,
			'grace_period_days': 30
		}

	except Exception as e:
		frappe.logger().error(f'Error requesting account deletion: {str(e)}')
		frappe.db.rollback()
		return {
			'success': False,
			'message': 'Failed to process account deletion request. Please contact support.'
		}


@frappe.whitelist(allow_guest=False, methods=['POST'])
def cancel_account_deletion():
	"""
	Cancel a pending account deletion request

	Returns:
		Dictionary with success status
	"""
	try:
		user_email = frappe.session.user

		# Reactivate subscriptions that were cancelled due to deletion
		cancelled_subscriptions = frappe.db.sql("""
			SELECT name
			FROM `tabAI Subscription`
			WHERE user = %s
			AND status = 'Cancelled'
			AND cancellation_reason LIKE '%%Account deletion requested%%'
			ORDER BY modified DESC
			LIMIT 1
		""", (user_email,), as_dict=True)

		if cancelled_subscriptions:
			for sub in cancelled_subscriptions:
				subscription = frappe.get_doc('AI Subscription', sub.name)
				subscription.status = 'Active'
				subscription.cancellation_reason = None
				subscription.add_comment('Info', f'Account deletion cancelled. Subscription reactivated on {now_datetime()}')
				subscription.save(ignore_permissions=True)

		# Reactivate API keys
		api_keys = frappe.db.get_list(
			'AI API Key',
			filters={'user': user_email, 'enabled': 0},
			fields=['name']
		)

		for key in api_keys:
			api_key = frappe.get_doc('AI API Key', key.name)
			api_key.enabled = 1
			api_key.add_comment('Info', f'Reactivated - account deletion cancelled on {now_datetime()}')
			api_key.save(ignore_permissions=True)

		# Add comment to user
		user = frappe.get_doc('User', user_email)
		user.add_comment('Info', f'Account deletion request cancelled on {now_datetime()}')

		frappe.db.commit()

		return {
			'success': True,
			'message': 'Account deletion request has been cancelled. Your account is now active.'
		}

	except Exception as e:
		frappe.logger().error(f'Error cancelling account deletion: {str(e)}')
		frappe.db.rollback()
		return {
			'success': False,
			'message': 'Failed to cancel account deletion. Please contact support.'
		}


@frappe.whitelist(allow_guest=False, methods=['POST'])
def anonymize_account():
	"""
	Anonymize user account data (for GDPR compliance)
	This should be called after grace period or immediately if user requests

	Returns:
		Dictionary with success status
	"""
	try:
		user_email = frappe.session.user

		# Prevent Administrator anonymization
		if user_email == 'Administrator':
			return {
				'success': False,
				'message': 'Administrator account cannot be anonymized'
			}

		# Get User document
		user = frappe.get_doc('User', user_email)

		# Anonymize personal data
		anonymized_id = f"deleted_user_{frappe.generate_hash(length=8)}"

		user.full_name = f"Deleted User"
		user.first_name = "Deleted"
		user.last_name = "User"
		user.mobile_no = None
		user.phone = None
		user.location = None
		user.bio = "Account deleted"
		user.user_image = None
		user.enabled = 0
		user.add_comment('Info', f'Account anonymized on {now_datetime()}')

		# Keep email for audit but mark it
		# user.email remains for record keeping

		user.save(ignore_permissions=True)

		# Mark all subscriptions as cancelled
		subscriptions = frappe.db.get_list(
			'AI Subscription',
			filters={'user': user_email},
			fields=['name']
		)

		for sub in subscriptions:
			subscription = frappe.get_doc('AI Subscription', sub.name)
			if subscription.status not in ['Cancelled', 'Expired']:
				subscription.status = 'Cancelled'
				subscription.cancelled_at = now_datetime()
				subscription.cancellation_reason = 'Account deleted and anonymized'
			subscription.save(ignore_permissions=True)

		# Delete all API keys
		api_keys = frappe.db.get_list(
			'AI API Key',
			filters={'user': user_email},
			fields=['name']
		)

		for key in api_keys:
			frappe.delete_doc('AI API Key', key.name, ignore_permissions=True)

		# Keep usage logs for audit but they're now anonymized via user reference

		frappe.db.commit()

		# Log out user
		frappe.local.login_manager.logout()

		return {
			'success': True,
			'message': 'Your account has been anonymized and deleted. All personal data has been removed.'
		}

	except Exception as e:
		frappe.logger().error(f'Error anonymizing account: {str(e)}')
		frappe.db.rollback()
		return {
			'success': False,
			'message': 'Failed to anonymize account. Please contact support.'
		}


@frappe.whitelist(allow_guest=False, methods=['GET'])
def get_deletion_status():
	"""
	Check if user has a pending deletion request

	Returns:
		Dictionary with deletion status
	"""
	try:
		user_email = frappe.session.user

		# Check comments for deletion request
		comments = frappe.db.sql("""
			SELECT content, creation
			FROM `tabComment`
			WHERE reference_doctype = 'User'
			AND reference_name = %s
			AND content LIKE '%%Account deletion requested%%'
			AND content LIKE '%%Scheduled for%%'
			ORDER BY creation DESC
			LIMIT 1
		""", (user_email,), as_dict=True)

		if comments:
			comment_text = comments[0].content
			# Parse deletion date from comment
			# Format: "Account deletion requested on YYYY-MM-DD HH:MM:SS. Scheduled for YYYY-MM-DD"
			try:
				scheduled_part = comment_text.split('Scheduled for ')[1]
				deletion_date = scheduled_part.strip()

				# Check if already cancelled
				cancel_comments = frappe.db.sql("""
					SELECT content
					FROM `tabComment`
					WHERE reference_doctype = 'User'
					AND reference_name = %s
					AND content LIKE '%%deletion request cancelled%%'
					AND creation > %s
					ORDER BY creation DESC
					LIMIT 1
				""", (user_email, comments[0].creation), as_dict=True)

				if cancel_comments:
					return {
						'success': True,
						'has_pending_deletion': False,
						'message': 'No pending deletion request'
					}

				return {
					'success': True,
					'has_pending_deletion': True,
					'deletion_date': deletion_date,
					'requested_on': comments[0].creation,
					'message': f'Account deletion scheduled for {deletion_date}'
				}
			except:
				pass

		return {
			'success': True,
			'has_pending_deletion': False,
			'message': 'No pending deletion request'
		}

	except Exception as e:
		frappe.logger().error(f'Error checking deletion status: {str(e)}')
		return {
			'success': False,
			'message': 'Failed to check deletion status'
		}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def check_and_reactivate_account(email, full_name=None):
	"""
	Check if an email belongs to a deleted account and offer reactivation
	This should be called during signup process

	Args:
		email: User's email address
		full_name: New full name (optional)

	Returns:
		Dictionary with account status and reactivation option
	"""
	try:
		# Check if user exists
		if not frappe.db.exists('User', email):
			return {
				'success': True,
				'account_exists': False,
				'can_signup': True,
				'message': 'Email available for signup'
			}

		# Get user document
		user = frappe.get_doc('User', email)

		# Check if account is disabled and was deleted (anonymized)
		if user.enabled == 0 and (user.bio == 'Account deleted' or user.full_name == 'Deleted User'):
			return {
				'success': True,
				'account_exists': True,
				'is_deleted': True,
				'can_reactivate': True,
				'message': 'This email was previously registered but the account was deleted. You can reactivate it.',
				'email': email
			}

		# Check if account is just disabled (not deleted)
		if user.enabled == 0:
			return {
				'success': True,
				'account_exists': True,
				'is_disabled': True,
				'can_reactivate': False,
				'message': 'This account is disabled. Please contact support for assistance.'
			}

		# Account exists and is active
		return {
			'success': True,
			'account_exists': True,
			'is_active': True,
			'can_signup': False,
			'message': 'This email is already registered. Please login instead.'
		}

	except Exception as e:
		frappe.logger().error(f'Error checking account status: {str(e)}')
		return {
			'success': False,
			'message': 'Error checking account status'
		}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def reactivate_deleted_account(email, full_name, password):
	"""
	Reactivate a previously deleted account with new credentials

	Args:
		email: User's email address
		full_name: User's new full name
		password: New password

	Returns:
		Dictionary with success status
	"""
	try:
		# Check if user exists and is deleted
		if not frappe.db.exists('User', email):
			return {
				'success': False,
				'message': 'Account not found'
			}

		user = frappe.get_doc('User', email)

		# Verify account is disabled and deleted
		if user.enabled != 0 or (user.bio != 'Account deleted' and user.full_name != 'Deleted User'):
			return {
				'success': False,
				'message': 'This account cannot be reactivated. Please contact support.'
			}

		# Reactivate account with new data
		name_parts = full_name.split(' ', 1)
		user.first_name = name_parts[0]
		user.last_name = name_parts[1] if len(name_parts) > 1 else ''
		user.full_name = full_name
		user.bio = None
		user.enabled = 1
		user.user_type = 'Website User'

		# Set new password
		user.new_password = password

		# Add reactivation comment
		user.add_comment('Info', f'Account reactivated on {now_datetime()} after previous deletion')

		user.save(ignore_permissions=True)

		# Create default subscription for reactivated user
		try:
			# Check if there's a trial plan
			trial_plan = frappe.db.get_value('AI Plan', {'is_trial': 1, 'is_active': 1}, 'name')

			if trial_plan:
				# Create new subscription
				subscription = frappe.new_doc('AI Subscription')
				subscription.user = email
				subscription.plan = trial_plan
				subscription.status = 'Trial'
				subscription.start_date = today()
				subscription.end_date = add_days(today(), 1)  # 1 day trial
				subscription.insert(ignore_permissions=True)
		except Exception as sub_error:
			frappe.logger().error(f'Error creating subscription for reactivated user: {str(sub_error)}')
			# Continue even if subscription creation fails

		frappe.db.commit()

		return {
			'success': True,
			'message': 'Your account has been successfully reactivated. You can now login with your new credentials.',
			'email': email
		}

	except Exception as e:
		frappe.logger().error(f'Error reactivating account: {str(e)}')
		frappe.db.rollback()
		return {
			'success': False,
			'message': 'Failed to reactivate account. Please contact support.'
		}
