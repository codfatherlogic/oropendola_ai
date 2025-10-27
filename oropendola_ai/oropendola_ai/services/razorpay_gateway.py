# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Razorpay Payment Gateway Integration
Handles payment processing, webhooks, and invoice reconciliation.
"""

import frappe
import os
import hashlib
import hmac
import json


class RazorpayGateway:
	"""
	Razorpay payment gateway integration.
	Handles order creation, payment verification, and webhooks.
	"""
	
	def __init__(self):
		self.key_id = os.getenv("RAZORPAY_KEY_ID")
		self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
		self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
		
		if not all([self.key_id, self.key_secret]):
			frappe.throw("Razorpay credentials not configured in environment")
		
		try:
			import razorpay
			self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
		except ImportError:
			frappe.throw("razorpay package not installed. Run: pip install razorpay")
	
	def create_order(self, invoice_id: str) -> dict:
		"""
		Create a Razorpay order for an invoice.
		
		Args:
			invoice_id (str): AI Invoice ID
			
		Returns:
			dict: Razorpay order details
		"""
		try:
			invoice = frappe.get_doc("AI Invoice", invoice_id)
			
			# Convert amount to paise (Razorpay uses smallest currency unit)
			amount_paise = int(invoice.total_amount * 100)
			
			# Create order
			order = self.client.order.create({
				"amount": amount_paise,
				"currency": invoice.currency or "INR",
				"receipt": invoice_id,
				"notes": {
					"invoice_id": invoice_id,
					"customer": invoice.customer,
					"subscription": invoice.subscription or ""
				}
			})
			
			# Update invoice with order ID
			invoice.payment_gateway_order_id = order["id"]
			invoice.payment_gateway = "Razorpay"
			invoice.status = "Pending"
			invoice.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"order_id": order["id"],
				"amount": amount_paise,
				"currency": order["currency"],
				"key_id": self.key_id
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to create Razorpay order: {str(e)}", "Razorpay Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def verify_payment(self, order_id: str, payment_id: str, signature: str) -> dict:
		"""
		Verify Razorpay payment signature.
		
		Args:
			order_id (str): Razorpay order ID
			payment_id (str): Razorpay payment ID
			signature (str): Payment signature
			
		Returns:
			dict: Verification result
		"""
		try:
			# Verify signature
			payload = f"{order_id}|{payment_id}"
			expected_signature = hmac.new(
				self.key_secret.encode(),
				payload.encode(),
				hashlib.sha256
			).hexdigest()
			
			if signature != expected_signature:
				return {
					"success": False,
					"error": "Invalid payment signature"
				}
			
			# Fetch payment details
			payment = self.client.payment.fetch(payment_id)
			
			return {
				"success": True,
				"payment": payment,
				"status": payment["status"]
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to verify payment: {str(e)}", "Razorpay Verification Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def process_payment_success(self, order_id: str, payment_id: str, signature: str) -> dict:
		"""
		Process successful payment and update invoice.
		
		Args:
			order_id (str): Razorpay order ID
			payment_id (str): Razorpay payment ID
			signature (str): Payment signature
			
		Returns:
			dict: Processing result
		"""
		try:
			# Verify payment
			verification = self.verify_payment(order_id, payment_id, signature)
			
			if not verification["success"]:
				return verification
			
			# Find invoice by order ID
			invoices = frappe.get_all(
				"AI Invoice",
				filters={"payment_gateway_order_id": order_id},
				fields=["name"]
			)
			
			if not invoices:
				return {
					"success": False,
					"error": "Invoice not found for order ID"
				}
			
			invoice = frappe.get_doc("AI Invoice", invoices[0].name)
			
			# Get payment method from payment object
			payment = verification["payment"]
			payment_method = payment.get("method", "").replace("_", " ").title()
			
			# Mark invoice as paid
			invoice.mark_as_paid(
				payment_id=payment_id,
				payment_method=payment_method,
				receipt_url=f"https://dashboard.razorpay.com/payments/{payment_id}"
			)
			
			return {
				"success": True,
				"invoice_id": invoice.name,
				"status": "Paid"
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to process payment success: {str(e)}", "Payment Processing Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def handle_webhook(self, payload: dict, signature: str) -> dict:
		"""
		Handle Razorpay webhook events.
		
		Args:
			payload (dict): Webhook payload
			signature (str): Webhook signature
			
		Returns:
			dict: Processing result
		"""
		try:
			# Verify webhook signature
			if self.webhook_secret:
				expected_signature = hmac.new(
					self.webhook_secret.encode(),
					json.dumps(payload).encode(),
					hashlib.sha256
				).hexdigest()
				
				if signature != expected_signature:
					frappe.log_error("Invalid webhook signature", "Razorpay Webhook Error")
					return {
						"success": False,
						"error": "Invalid signature"
					}
			
			# Process event
			event = payload.get("event")
			data = payload.get("payload", {}).get("payment", {}).get("entity", {})
			
			if event == "payment.captured":
				# Payment successful
				order_id = data.get("order_id")
				payment_id = data.get("id")
				
				# Find and update invoice
				invoices = frappe.get_all(
					"AI Invoice",
					filters={"payment_gateway_order_id": order_id},
					fields=["name"]
				)
				
				if invoices:
					invoice = frappe.get_doc("AI Invoice", invoices[0].name)
					invoice.mark_as_paid(payment_id=payment_id)
					
					frappe.logger().info(f"Payment captured for invoice {invoice.name}")
			
			elif event == "payment.failed":
				# Payment failed
				order_id = data.get("order_id")
				error_desc = data.get("error_description", "Payment failed")
				
				invoices = frappe.get_all(
					"AI Invoice",
					filters={"payment_gateway_order_id": order_id},
					fields=["name"]
				)
				
				if invoices:
					invoice = frappe.get_doc("AI Invoice", invoices[0].name)
					invoice.mark_as_failed(reason=error_desc)
					
					frappe.logger().info(f"Payment failed for invoice {invoice.name}: {error_desc}")
			
			return {
				"success": True,
				"event": event
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to handle webhook: {str(e)}", "Webhook Error")
			return {
				"success": False,
				"error": str(e)
			}


# Singleton gateway instance
_gateway = None

def get_gateway():
	"""Get singleton RazorpayGateway instance"""
	global _gateway
	if _gateway is None:
		_gateway = RazorpayGateway()
	return _gateway


@frappe.whitelist(allow_guest=False)
def create_payment_order(invoice_id: str):
	"""
	Create payment order for an invoice.
	
	Args:
		invoice_id (str): Invoice ID
		
	Returns:
		dict: Razorpay order details
	"""
	gateway = get_gateway()
	return gateway.create_order(invoice_id)


@frappe.whitelist(allow_guest=False)
def verify_payment_signature(order_id: str, payment_id: str, signature: str):
	"""
	Verify and process payment.
	
	Args:
		order_id (str): Razorpay order ID
		payment_id (str): Razorpay payment ID
		signature (str): Payment signature
		
	Returns:
		dict: Verification result
	"""
	gateway = get_gateway()
	return gateway.process_payment_success(order_id, payment_id, signature)


@frappe.whitelist(allow_guest=True)
def razorpay_webhook():
	"""
	Razorpay webhook endpoint.
	Handles payment events from Razorpay.
	"""
	try:
		# Get request data
		payload = frappe.request.get_json()
		signature = frappe.get_request_header("X-Razorpay-Signature")
		
		gateway = get_gateway()
		result = gateway.handle_webhook(payload, signature)
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Webhook processing failed: {str(e)}", "Razorpay Webhook Error")
		return {
			"success": False,
			"error": str(e)
		}
