# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Embedded Payment API
Handles payment sessions for embedded payment flows (PayU Bolt, Razorpay, Stripe)
"""

import frappe
from frappe import _
import json


@frappe.whitelist()
def initialize_payment_session(invoice_id: str, gateway: str = "PayU", embed_mode: bool = True):
	"""
	Initialize payment session for embedded payment flow

	Args:
		invoice_id: AI Invoice ID
		gateway: Payment gateway (PayU, Razorpay, Stripe)
		embed_mode: True for embedded, False for redirect

	Returns:
		dict: Session details with embed configuration
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Please login to continue with payment"
			}

		# Get invoice
		invoice = frappe.get_doc("AI Invoice", invoice_id)

		# Verify user owns this invoice
		if invoice.customer != user:
			return {
				"success": False,
				"error": "Unauthorized access to invoice"
			}

		# Check invoice status
		if invoice.status == "Paid":
			return {
				"success": False,
				"error": "Invoice is already paid",
				"paid": True
			}

		if invoice.status not in ["Pending", "Failed", "Abandoned"]:
			return {
				"success": False,
				"error": f"Invoice cannot be paid in current status: {invoice.status}"
			}

		# Check for active session
		from oropendola_ai.oropendola_ai.doctype.payment_session.payment_session import PaymentSession
		active_session = PaymentSession.get_active_session(invoice_id)

		if active_session:
			# Return existing session
			frappe.logger().info(f"Returning existing session {active_session.name} for invoice {invoice_id}")
			return _format_session_response(active_session, invoice)

		# Create new payment session
		session = frappe.get_doc({
			"doctype": "Payment Session",
			"user": user,
			"invoice": invoice_id,
			"gateway": gateway,
			"status": "Initiated",
			"amount": invoice.total_amount,
			"currency": invoice.currency or "INR",
			"embed_mode": 1 if embed_mode else 0
		})
		session.insert(ignore_permissions=True)

		# Mark invoice as processing
		invoice.mark_as_processing()

		# Get gateway-specific configuration
		gateway_config = _get_gateway_config(session, invoice, embed_mode)

		if not gateway_config.get("success"):
			session.mark_as_failed(gateway_config.get("error"))
			return gateway_config

		# Store gateway config in session
		session.set_session_data(gateway_config.get("config", {}))
		session.transaction_id = gateway_config.get("transaction_id")
		session.mark_as_pending()

		frappe.db.commit()

		frappe.logger().info(f"Created payment session {session.name} for invoice {invoice_id}")

		return {
			"success": True,
			"session_id": session.name,
			"invoice_id": invoice_id,
			"gateway": gateway,
			"embed_mode": embed_mode,
			"amount": float(invoice.total_amount),
			"currency": invoice.currency or "INR",
			"gateway_config": gateway_config.get("config", {}),
			"instructions": gateway_config.get("instructions", {}),
			"message": "Payment session created successfully"
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Initialize Payment Session Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_payment_session(session_id: str = None, invoice_id: str = None):
	"""
	Get payment session details

	Args:
		session_id: Payment Session ID (optional)
		invoice_id: Invoice ID to get active session (optional)

	Returns:
		dict: Session details
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Please login to view payment session"
			}

		# Get session by ID or invoice
		if session_id:
			session = frappe.get_doc("Payment Session", session_id)
		elif invoice_id:
			from oropendola_ai.oropendola_ai.doctype.payment_session.payment_session import PaymentSession
			session = PaymentSession.get_active_session(invoice_id)
			if not session:
				return {
					"success": False,
					"error": "No active payment session found"
				}
		else:
			return {
				"success": False,
				"error": "Please provide session_id or invoice_id"
			}

		# Verify user owns this session
		if session.user != user:
			return {
				"success": False,
				"error": "Unauthorized access to session"
			}

		invoice = frappe.get_doc("AI Invoice", session.invoice)

		return _format_session_response(session, invoice)

	except Exception as e:
		frappe.log_error(message=str(e), title="Get Payment Session Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def cancel_payment_session(session_id: str, reason: str = None):
	"""
	Cancel payment session when user cancels payment

	Args:
		session_id: Payment Session ID
		reason: Cancellation reason

	Returns:
		dict: Cancellation result
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Unauthorized"
			}

		session = frappe.get_doc("Payment Session", session_id)

		# Verify user owns this session
		if session.user != user:
			return {
				"success": False,
				"error": "Unauthorized access to session"
			}

		# Mark session as cancelled
		session.mark_as_cancelled(reason or "User cancelled payment")

		# Update invoice
		invoice = frappe.get_doc("AI Invoice", session.invoice)
		invoice.db_set("status", "Pending")  # Reset to pending for retry

		frappe.db.commit()

		return {
			"success": True,
			"session_id": session.name,
			"status": "Cancelled",
			"can_retry": session.can_retry(),
			"message": "Payment cancelled successfully"
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Cancel Payment Session Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def retry_payment_session(invoice_id: str, gateway: str = None):
	"""
	Retry payment for invoice with failed/cancelled session

	Args:
		invoice_id: AI Invoice ID
		gateway: Payment gateway (optional, uses previous if not provided)

	Returns:
		dict: New session details
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Please login to retry payment"
			}

		# Get invoice
		invoice = frappe.get_doc("AI Invoice", invoice_id)

		# Verify user owns this invoice
		if invoice.customer != user:
			return {
				"success": False,
				"error": "Unauthorized access to invoice"
			}

		# Get latest failed/cancelled session
		sessions = frappe.get_all(
			"Payment Session",
			filters={
				"invoice": invoice_id,
				"status": ["in", ["Failed", "Cancelled", "Abandoned"]]
			},
			fields=["name", "gateway", "attempt_count"],
			order_by="creation desc",
			limit=1
		)

		if not sessions:
			return {
				"success": False,
				"error": "No failed session found to retry"
			}

		last_session = frappe.get_doc("Payment Session", sessions[0].name)

		# Check if can retry
		if not last_session.can_retry():
			return {
				"success": False,
				"error": "Maximum retry attempts reached (3)",
				"max_attempts_reached": True
			}

		# Use provided gateway or previous gateway
		retry_gateway = gateway or last_session.gateway

		# Increment attempt counter
		last_session.increment_attempt()

		# Create new session
		return initialize_payment_session(
			invoice_id=invoice_id,
			gateway=retry_gateway,
			embed_mode=bool(last_session.embed_mode)
		)

	except Exception as e:
		frappe.log_error(message=str(e), title="Retry Payment Session Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def verify_payment_session(session_id: str, gateway_response: dict = None):
	"""
	Verify payment after user completes gateway flow
	Called by frontend after payment completion

	Args:
		session_id: Payment Session ID
		gateway_response: Gateway response data (optional)

	Returns:
		dict: Verification result
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Unauthorized"
			}

		session = frappe.get_doc("Payment Session", session_id)

		# Verify user owns this session
		if session.user != user:
			return {
				"success": False,
				"error": "Unauthorized access to session"
			}

		# Mark as processing
		session.mark_as_processing()

		# Verify with gateway based on gateway type
		verification = _verify_with_gateway(session, gateway_response)

		if not verification.get("success"):
			session.mark_as_failed(
				error_message=verification.get("error"),
				gateway_response=gateway_response
			)
			return verification

		# Mark session as success
		session.mark_as_success(
			transaction_id=verification.get("transaction_id"),
			gateway_response=gateway_response
		)

		# Apply payment to subscription
		from oropendola_ai.oropendola_ai.api.subscription_renewal import apply_payment_to_subscription
		result = apply_payment_to_subscription(session.invoice)

		if not result.get("success"):
			frappe.logger().error(f"Failed to apply payment for session {session_id}: {result.get('error')}")

		frappe.db.commit()

		return {
			"success": True,
			"session_id": session.name,
			"invoice_id": session.invoice,
			"subscription_id": result.get("subscription_id"),
			"transaction_id": session.transaction_id,
			"status": "Success",
			"message": "Payment verified and subscription activated"
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Verify Payment Session Error")
		return {
			"success": False,
			"error": str(e)
		}


def _get_gateway_config(session, invoice, embed_mode):
	"""Get gateway-specific configuration"""
	gateway = session.gateway

	if gateway == "PayU":
		from oropendola_ai.oropendola_ai.services.payu_gateway import PayUGateway
		gateway_obj = PayUGateway()

		if embed_mode:
			# Use Bolt for embedded
			config = gateway_obj.create_bolt_payment_request(invoice.name, embed_mode=True)
		else:
			# Use regular PayU for redirect
			config = gateway_obj.create_payment_request(invoice.name)

		return config

	elif gateway == "Razorpay":
		return {
			"success": False,
			"error": "Razorpay integration coming soon"
		}

	elif gateway == "Stripe":
		return {
			"success": False,
			"error": "Stripe integration coming soon"
		}

	else:
		return {
			"success": False,
			"error": f"Unknown payment gateway: {gateway}"
		}


def _verify_with_gateway(session, gateway_response):
	"""Verify payment with gateway"""
	gateway = session.gateway

	if gateway == "PayU":
		# PayU verification is handled by webhook callback
		# This is a frontend-initiated verification for immediate feedback
		# Real verification happens in webhook handler

		# For now, trust the gateway response if it indicates success
		# Actual verification happens in payu_callback
		if gateway_response and gateway_response.get("status") == "success":
			return {
				"success": True,
				"transaction_id": gateway_response.get("txnid") or gateway_response.get("mihpayid")
			}
		else:
			return {
				"success": False,
				"error": gateway_response.get("error") or "Payment verification failed"
			}

	elif gateway == "Razorpay":
		return {
			"success": False,
			"error": "Razorpay verification not implemented"
		}

	elif gateway == "Stripe":
		return {
			"success": False,
			"error": "Stripe verification not implemented"
		}

	else:
		return {
			"success": False,
			"error": f"Unknown gateway: {gateway}"
		}


def _format_session_response(session, invoice):
	"""Format session response for API"""
	return {
		"success": True,
		"session": {
			"id": session.name,
			"invoice_id": session.invoice,
			"gateway": session.gateway,
			"status": session.status,
			"amount": float(session.amount),
			"currency": session.currency,
			"embed_mode": bool(session.embed_mode),
			"transaction_id": session.transaction_id,
			"attempt_count": session.attempt_count or 1,
			"can_retry": session.can_retry(),
			"last_attempt_at": str(session.last_attempt_at) if session.last_attempt_at else None,
			"created_at": str(session.creation),
			"session_data": session.get_session_data()
		},
		"invoice": {
			"id": invoice.name,
			"status": invoice.status,
			"amount": float(invoice.total_amount),
			"plan": invoice.plan
		}
	}


@frappe.whitelist()
def get_user_payment_sessions(limit: int = 10):
	"""
	Get recent payment sessions for current user

	Args:
		limit: Number of sessions to return

	Returns:
		dict: List of payment sessions
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			return {
				"success": False,
				"error": "Please login to view sessions"
			}

		from oropendola_ai.oropendola_ai.doctype.payment_session.payment_session import PaymentSession
		sessions = PaymentSession.get_user_sessions(user, limit=limit)

		return {
			"success": True,
			"sessions": sessions,
			"count": len(sessions)
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Get User Sessions Error")
		return {
			"success": False,
			"error": str(e)
		}
