# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class PaymentSession(Document):
	"""
	Payment Session tracking for embedded payment flows.
	Tracks payment attempts, retries, and gateway-specific data.
	"""

	def before_insert(self):
		"""Initialize session before insert"""
		self.attempt_count = 1
		self.last_attempt_at = frappe.utils.now()

		# Capture client metadata
		if frappe.request:
			self.client_ip = frappe.local.request_ip or None
			self.user_agent = frappe.request.headers.get('User-Agent', '')[:500]

	def validate(self):
		"""Validate payment session data"""
		# Ensure amount matches invoice
		if self.invoice:
			invoice = frappe.get_doc("AI Invoice", self.invoice)
			if float(self.amount) != float(invoice.total_amount):
				frappe.throw("Session amount must match invoice amount")

	def mark_as_pending(self):
		"""Mark session as pending after gateway redirect/embed"""
		self.status = "Pending"
		self.save(ignore_permissions=True)
		frappe.db.commit()

	def mark_as_processing(self):
		"""Mark session as processing when payment is in progress"""
		self.status = "Processing"
		self.last_attempt_at = frappe.utils.now()
		self.save(ignore_permissions=True)
		frappe.db.commit()

	def mark_as_success(self, transaction_id=None, gateway_response=None):
		"""Mark session as successful"""
		self.status = "Success"
		self.last_attempt_at = frappe.utils.now()

		if transaction_id:
			self.transaction_id = transaction_id

		if gateway_response:
			self.gateway_response = json.dumps(gateway_response) if isinstance(gateway_response, dict) else str(gateway_response)

		self.save(ignore_permissions=True)
		frappe.db.commit()

	def mark_as_failed(self, error_message=None, gateway_response=None):
		"""Mark session as failed"""
		self.status = "Failed"
		self.last_attempt_at = frappe.utils.now()

		if error_message:
			self.error_message = str(error_message)[:500]

		if gateway_response:
			self.gateway_response = json.dumps(gateway_response) if isinstance(gateway_response, dict) else str(gateway_response)

		self.save(ignore_permissions=True)
		frappe.db.commit()

	def mark_as_cancelled(self, reason=None):
		"""Mark session as cancelled by user"""
		self.status = "Cancelled"
		self.last_attempt_at = frappe.utils.now()

		if reason:
			self.error_message = str(reason)[:500]

		self.save(ignore_permissions=True)
		frappe.db.commit()

	def mark_as_abandoned(self, reason=None):
		"""Mark session as abandoned (no response after timeout)"""
		self.status = "Abandoned"

		if reason:
			self.error_message = str(reason)[:500]

		self.save(ignore_permissions=True)
		frappe.db.commit()

	def increment_attempt(self):
		"""Increment retry attempt counter"""
		self.attempt_count = (self.attempt_count or 0) + 1
		self.last_attempt_at = frappe.utils.now()
		self.status = "Initiated"  # Reset to initiated for retry
		self.save(ignore_permissions=True)
		frappe.db.commit()

	def can_retry(self):
		"""Check if session can be retried"""
		max_attempts = 3
		return self.status in ["Failed", "Cancelled", "Abandoned"] and (self.attempt_count or 0) < max_attempts

	def get_session_data(self):
		"""Get parsed session data"""
		if self.session_data:
			try:
				return json.loads(self.session_data)
			except:
				return {}
		return {}

	def set_session_data(self, data):
		"""Set session data as JSON"""
		self.session_data = json.dumps(data) if isinstance(data, dict) else str(data)

	@staticmethod
	def get_active_session(invoice_id):
		"""Get active payment session for invoice"""
		sessions = frappe.get_all(
			"Payment Session",
			filters={
				"invoice": invoice_id,
				"status": ["in", ["Initiated", "Pending", "Processing"]]
			},
			fields=["name", "status", "gateway", "attempt_count"],
			order_by="creation desc",
			limit=1
		)

		if sessions:
			return frappe.get_doc("Payment Session", sessions[0].name)

		return None

	@staticmethod
	def get_user_sessions(user, limit=10):
		"""Get recent payment sessions for user"""
		return frappe.get_all(
			"Payment Session",
			filters={"user": user},
			fields=["name", "invoice", "gateway", "status", "amount", "currency", "creation", "modified"],
			order_by="creation desc",
			limit=limit
		)
