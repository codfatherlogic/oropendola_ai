# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Payment API Endpoints
Handles subscription purchase flow, payment processing, and callbacks
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=True)
def get_plans():
	"""
	Get all active subscription plans
	
	Returns:
		list: Active plans with details
	"""
	try:
		plans = frappe.get_all(
			"AI Plan",
			filters={"is_active": 1},
			fields=[
				"name", "plan_id", "title", "description", "price", "currency",
				"duration_days", "requests_limit_per_day", "monthly_budget_limit",
				"support_level", "default_routing_mode"
			],
			order_by="price asc"
		)
		
		# Get features and models for each plan
		for plan in plans:
			try:
				# Get features
				features = frappe.get_all(
					"AI Plan Feature",
					filters={"parent": plan["name"], "enabled": 1},
					fields=["feature_name"],
					order_by="idx"
				)
				plan["features"] = features if features else []
				
				# Get model access
				models = frappe.get_all(
					"AI Plan Model Access",
					filters={"parent": plan["name"]},
					fields=["model_name"],
					order_by="idx"
				)
				plan["models"] = models if models else []
			except Exception as child_error:
				frappe.log_error(f"Error getting plan details for {plan['name']}: {str(child_error)}")
				plan["features"] = []
				plan["models"] = []
		
		return {
			"success": True,
			"plans": plans
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Get Plans Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def create_subscription_and_invoice(plan_id: str):
	"""
	Create subscription and invoice for logged-in user
	
	Args:
		plan_id (str): Plan ID to subscribe to
		
	Returns:
		dict: Subscription and invoice details
	"""
	try:
		user = frappe.session.user
		
		if user == "Guest":
			frappe.throw(_("Please login to subscribe"))
		
		# Check if user already has an active subscription
		existing = frappe.get_all(
			"AI Subscription",
			filters={
				"user": user,
				"status": ["in", ["Active", "Trial"]]
			},
			fields=["name", "plan", "status"]
		)
		
		if existing:
			return {
				"success": False,
				"error": "You already have an active subscription",
				"existing_subscription": existing[0]
			}
		
		# Get plan
		plan = frappe.get_doc("AI Plan", plan_id)
		
		if not plan.is_active:
			frappe.throw(_("This plan is not available"))
		
		# Check if it's a free plan
		if float(plan.price or 0) == 0:
			# Create subscription directly without payment
			subscription = create_free_subscription(user, plan)
			return {
				"success": True,
				"is_free": True,
				"subscription_id": subscription.name,
				"status": "Active"
			}
		
		# Create subscription in pending state with exact datetime
		start_datetime = frappe.utils.now()
		end_datetime = frappe.utils.add_to_date(start_datetime, days=plan.duration_days) if (plan.duration_days and plan.duration_days > 0) else None

		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"user": user,
			"plan": plan.name,
			"status": "Pending",
			"start_date": start_datetime,
			"end_date": end_datetime,
			"billing_email": frappe.db.get_value("User", user, "email"),
			"daily_quota_limit": plan.requests_limit_per_day,
			"daily_quota_remaining": plan.requests_limit_per_day,
			"auto_renew": 0,  # Auto-renewal disabled by default
			"created_by_user": user
		})
		subscription.insert(ignore_permissions=True)
		
		# Create invoice
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": user,
			"subscription": subscription.name,
			"plan": plan.name,
			"status": "Pending",
			"invoice_date": frappe.utils.today(),
			"due_date": frappe.utils.add_days(frappe.utils.today(), 7),
			"period_start": start_datetime,
			"period_end": end_datetime,
			"billing_type": "Subscription",
			"amount_due": plan.price or 0,
			"total_amount": plan.price or 0,
			"base_plan_amount": plan.price or 0,
			"currency": plan.currency or "INR",
			"payment_gateway": "PayU"
		})
		invoice.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return {
			"success": True,
			"is_free": False,
			"subscription_id": subscription.name,
			"invoice_id": invoice.name,
			"amount": float(plan.price),
			"currency": plan.currency or "INR"
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Create Subscription Error")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e)
		}


def create_free_subscription(user, plan):
	"""Create and activate free subscription with exact datetime"""
	start_datetime = frappe.utils.now()
	end_datetime = frappe.utils.add_to_date(start_datetime, days=plan.duration_days) if (plan.duration_days and plan.duration_days > 0) else None

	subscription = frappe.get_doc({
		"doctype": "AI Subscription",
		"user": user,
		"plan": plan.name,
		"status": "Active",
		"start_date": start_datetime,
		"end_date": end_datetime,
		"billing_email": frappe.db.get_value("User", user, "email"),
		"daily_quota_limit": plan.requests_limit_per_day,
		"daily_quota_remaining": plan.requests_limit_per_day,
		"auto_renew": 0,
		"created_by_user": user,
		"amount_paid": 0,
		"last_payment_date": frappe.utils.now()
	})
	subscription.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return subscription


@frappe.whitelist()
def create_invoice_for_subscription(subscription_id: str):
	"""
	Create invoice for an existing subscription
	
	Args:
		subscription_id (str): Subscription ID
		
	Returns:
		dict: Invoice details
	"""
	try:
		user = frappe.session.user
		
		if user == "Guest":
			frappe.throw(_("Please login to continue"))
		
		# Get subscription
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Verify subscription belongs to user
		if subscription.user != user:
			frappe.throw(_("Unauthorized access"))
		
		# Get plan
		plan = frappe.get_doc("AI Plan", subscription.plan)
		
		# Check if it's a free plan
		if float(plan.price or 0) == 0:
			# Activate free subscription immediately
			subscription.db_set("status", "Active")
			frappe.db.commit()
			return {
				"success": True,
				"is_free": True,
				"subscription_id": subscription.name
			}
		
		# Check if invoice already exists for this subscription
		existing_invoice = frappe.get_all(
			"AI Invoice",
			filters={
				"subscription": subscription_id,
				"status": ["in", ["Pending", "Processing"]]
			},
			fields=["name"],
			limit=1
		)
		
		if existing_invoice:
			return {
				"success": True,
				"is_free": False,
				"invoice_id": existing_invoice[0].name,
				"amount": float(plan.price),
				"currency": plan.currency or "INR"
			}
		
		# Create new invoice
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": user,
			"subscription": subscription.name,
			"plan": plan.name,
			"status": "Pending",
			"invoice_date": frappe.utils.today(),
			"due_date": frappe.utils.add_days(frappe.utils.today(), 7),
			"period_start": subscription.start_date,
			"period_end": subscription.end_date,
			"billing_type": "Subscription",
			"amount_due": plan.price or 0,
			"total_amount": plan.price or 0,
			"base_plan_amount": plan.price or 0,
			"currency": plan.currency or "INR",
			"payment_gateway": "PayU"
		})
		invoice.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return {
			"success": True,
			"is_free": False,
			"invoice_id": invoice.name,
			"amount": float(plan.price),
			"currency": plan.currency or "INR"
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Create Invoice Error")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def initiate_payment(invoice_id: str, gateway: str = "payu"):
	"""
	Initiate payment for an invoice
	
	Args:
		invoice_id (str): Invoice ID
		gateway (str): Payment gateway (payu/razorpay)
		
	Returns:
		dict: Payment initiation details
	"""
	try:
		user = frappe.session.user
		
		# Verify invoice belongs to user
		invoice = frappe.get_doc("AI Invoice", invoice_id)
		if invoice.customer != user:
			frappe.throw(_("Unauthorized access"))
		
		if invoice.status == "Paid":
			return {
				"success": False,
				"error": "Invoice already paid"
			}
		
		# Get payment gateway
		gateway = gateway.lower()
		
		if gateway == "payu":
			from oropendola_ai.oropendola_ai.services.payu_gateway import get_gateway
			payu = get_gateway()
			# Use PayU redirect mode (hosted checkout)
			return payu.create_payment_request(invoice_id)
		elif gateway == "razorpay":
			from oropendola_ai.oropendola_ai.services.razorpay_gateway import get_gateway
			rzp = get_gateway()
			return rzp.create_order(invoice_id)
		else:
			frappe.throw(_("Invalid payment gateway"))
			
	except Exception as e:
		frappe.log_error(message=str(e), title="Initiate Payment Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def payu_success():
	"""
	PayU payment success callback
	"""
	try:
		# Get POST data and convert to regular dict
		data = dict(frappe.form_dict)

		# Process payment
		from oropendola_ai.oropendola_ai.services.payu_gateway import get_gateway
		gateway = get_gateway()
		result = gateway.process_payment_success(data)
		
		if result["success"]:
			# Show success message
			frappe.msgprint(
				msg=f"Payment successful! Your subscription is now active.",
				title="Payment Successful",
				indicator="green"
			)

			# Redirect to user profile page
			success_url = "/profile"
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = success_url
		else:
			# Redirect to failure page
			failure_url = f"/payment-failed?error={result.get('error')}"
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = failure_url
			
	except Exception as e:
		frappe.log_error(message=str(e), title="PayU Success Callback Error")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"/payment-failed?error=Processing error"


@frappe.whitelist(allow_guest=True)
def payu_failure():
	"""
	PayU payment failure callback
	"""
	try:
		# Get POST data and convert to regular dict
		data = dict(frappe.form_dict)

		# Process failure
		from oropendola_ai.oropendola_ai.services.payu_gateway import get_gateway
		gateway = get_gateway()
		result = gateway.process_payment_failure(data)
		
		# Redirect to failure page
		error_msg = result.get("error", "Payment failed")
		failure_url = f"/payment-failed?error={error_msg}&invoice={result.get('invoice_id')}"
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = failure_url
		
	except Exception as e:
		frappe.log_error(message=str(e), title="PayU Failure Callback Error")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"/payment-failed?error=Processing error"


@frappe.whitelist()
def get_my_subscription():
	"""
	Get current user's active subscription
	
	Returns:
		dict: Subscription details
	"""
	try:
		user = frappe.session.user
		
		if user == "Guest":
			return {
				"success": False,
				"error": "Please login"
			}
		
		# Get active subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={
				"user": user,
				"status": ["in", ["Active", "Trial"]]
			},
			fields=["*"],
			limit=1
		)
		
		if not subscriptions:
			return {
				"success": True,
				"has_subscription": False
			}
		
		subscription = subscriptions[0]
		
		# Get plan details
		plan = frappe.get_doc("AI Plan", subscription["plan"])
		
		return {
			"success": True,
			"has_subscription": True,
			"subscription": subscription,
			"plan": {
				"name": plan.name,
				"title": plan.title,
				"price": plan.price,
				"requests_limit_per_day": plan.requests_limit_per_day
			}
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Get Subscription Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def cancel_subscription(subscription_id: str, reason: str = ""):
	"""
	Cancel user's subscription
	
	Args:
		subscription_id (str): Subscription ID
		reason (str): Cancellation reason
		
	Returns:
		dict: Cancellation result
	"""
	try:
		user = frappe.session.user
		
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		if subscription.user != user:
			frappe.throw(_("Unauthorized access"))
		
		subscription.db_set("status", "Cancelled")
		subscription.db_set("cancelled_at", frappe.utils.now())
		subscription.db_set("cancellation_reason", reason)
		frappe.db.commit()
		
		return {
			"success": True,
			"message": "Subscription cancelled successfully"
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Cancel Subscription Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_available_gateways():
	"""
	Get list of configured payment gateways

	Returns:
		dict: Available payment gateways with their status
	"""
	try:
		gateways = []

		# Check PayU configuration from Oropendola Settings
		settings = frappe.get_single("Oropendola Settings")
		payu_key = settings.payu_merchant_key
		payu_salt = settings.get_password("payu_merchant_salt")

		if payu_key and payu_salt:
			gateways.append({
				"id": "payu",
				"name": "PayU",
				"available": True,
				"recommended": True,
				"methods": ["upi", "cards", "netbanking", "wallets"]
			})

		return {
			"success": True,
			"gateways": gateways,
			"default": "payu" if gateways else None
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Get Gateways Error")
		return {
			"success": False,
			"error": str(e),
			"gateways": []
		}


@frappe.whitelist()
def retry_payment(invoice_id: str, gateway: str = "payu"):
	"""
	Retry payment for a failed or abandoned invoice

	Args:
		invoice_id (str): Invoice ID to retry
		gateway (str): Payment gateway to use

	Returns:
		dict: Payment initiation details or error
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			frappe.throw(_("Please login to retry payment"))

		# Get invoice
		invoice = frappe.get_doc("AI Invoice", invoice_id)

		# Verify invoice belongs to user
		if invoice.customer != user:
			frappe.throw(_("Unauthorized access"))

		# Check if invoice can be retried
		if not invoice.can_retry():
			return {
				"success": False,
				"error": f"Cannot retry invoice. Status: {invoice.status}, Retry count: {invoice.retry_count or 0}/3"
			}

		# Increment retry counter and reset status to Pending
		invoice.increment_retry()
		frappe.db.commit()

		# Initiate payment again
		return initiate_payment(invoice_id, gateway)

	except Exception as e:
		frappe.log_error(message=str(e), title="Retry Payment Error")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_pending_invoices():
	"""
	Get user's pending/processing/abandoned invoices that can be retried

	Returns:
		dict: List of invoices with retry information
	"""
	try:
		user = frappe.session.user

		if user == "Guest":
			frappe.throw(_("Please login to view invoices"))

		# Get invoices that can be retried
		invoices = frappe.get_all(
			"AI Invoice",
			filters={
				"customer": user,
				"status": ["in", ["Pending", "Processing", "Abandoned", "Failed"]]
			},
			fields=["name", "status", "total_amount", "currency", "invoice_date", "retry_count", "plan"],
			order_by="creation desc"
		)

		# Add retry capability flag
		for invoice in invoices:
			invoice_doc = frappe.get_doc("AI Invoice", invoice.name)
			invoice["can_retry"] = invoice_doc.can_retry()

		return {
			"success": True,
			"invoices": invoices,
			"count": len(invoices)
		}

	except Exception as e:
		frappe.log_error(message=str(e), title="Get Pending Invoices Error")
		return {
			"success": False,
			"error": str(e)
		}


def check_abandoned_payments():
	"""
	Check for abandoned payment sessions and mark them as abandoned.
	Runs every 30 minutes via scheduler.

	Marks as abandoned if:
	- Invoice is still Pending and created more than 1 hour ago
	- Associated subscription is still Pending

	This handles cases where user:
	- Closes browser without completing payment
	- Abandons PayU payment page
	- Does not return from PayU (no callback received)
	"""
	try:
		from frappe.utils import add_to_date, now

		frappe.logger().info("Checking for abandoned payments...")

		# Find invoices that are still pending after 1 hour
		cutoff_time = add_to_date(now(), hours=-1)

		abandoned_invoices = frappe.get_all(
			"AI Invoice",
			filters={
				"status": "Pending",
				"creation": ["<", cutoff_time]
			},
			fields=["name", "subscription", "customer", "total_amount"]
		)

		count = 0
		for inv in abandoned_invoices:
			try:
				# Get invoice
				invoice = frappe.get_doc("AI Invoice", inv.name)

				# Mark invoice as abandoned
				invoice.db_set("status", "Abandoned", update_modified=False)
				frappe.logger().info(f"Invoice {invoice.name} marked as Abandoned")

				# Cancel associated pending subscription
				if invoice.subscription:
					subscription = frappe.get_doc("AI Subscription", invoice.subscription)
					if subscription.status == "Pending":
						subscription.db_set("status", "Cancelled", update_modified=False)
						subscription.db_set("cancellation_reason", "Payment abandoned - no payment received within 1 hour", update_modified=False)
						frappe.logger().info(f"Subscription {subscription.name} cancelled due to abandoned payment")

				count += 1

			except Exception as invoice_error:
				frappe.log_error(
					message=str(invoice_error),
					title=f"Error processing abandoned invoice {inv.name}"
				)
				continue

		frappe.db.commit()
		frappe.logger().info(f"Marked {count} abandoned payments")

	except Exception as e:
		frappe.log_error(f"Failed to check abandoned payments: {str(e)}", "Abandoned Payments Check Error")
