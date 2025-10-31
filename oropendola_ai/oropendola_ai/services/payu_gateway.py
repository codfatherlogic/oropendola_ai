# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
PayU Payment Gateway Integration
Implements PayU Money payment gateway for Indian market
Reference: https://docs.payu.in/reference/introduction-api-reference
"""

import frappe
import hashlib
import requests
import json
from typing import Dict, Optional


class PayUGateway:
	"""
	PayU payment gateway integration for India.
	Supports payment processing, verification, and webhooks.
	"""
	
	def __init__(self):
		"""Initialize PayU gateway with credentials from Oropendola Settings"""
		# Get credentials from Oropendola Settings
		settings = frappe.get_single("Oropendola Settings")
		self.merchant_key = settings.payu_merchant_key
		self.merchant_salt = settings.get_password("payu_merchant_salt")
		self.mode = settings.payu_mode or "test"

		if not all([self.merchant_key, self.merchant_salt]):
			frappe.throw("PayU credentials not configured. Please configure PayU settings in Oropendola Settings")

		# Set endpoint based on mode
		if self.mode == "production":
			self.base_url = "https://secure.payu.in"
		else:
			self.base_url = "https://test.payu.in"
	
	def generate_hash(self, data: dict) -> str:
		"""
		Generate PayU payment hash
		Formula: sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
		
		Args:
			data (dict): Payment data
			
		Returns:
			str: SHA512 hash
		"""
		hash_string = (
			f"{self.merchant_key}|{data['txnid']}|{data['amount']}|"
			f"{data['productinfo']}|{data['firstname']}|{data['email']}|"
			f"{data.get('udf1', '')}|{data.get('udf2', '')}|{data.get('udf3', '')}|"
			f"{data.get('udf4', '')}|{data.get('udf5', '')}||||||{self.merchant_salt}"
		)
		return hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
	
	def verify_hash(self, data: dict) -> bool:
		"""
		Verify PayU response hash
		Formula: sha512(SALT|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)
		
		Args:
			data (dict): Response data from PayU
			
		Returns:
			bool: True if hash is valid
		"""
		hash_string = (
			f"{self.merchant_salt}|{data.get('status', '')}||||||"
			f"{data.get('udf5', '')}|{data.get('udf4', '')}|{data.get('udf3', '')}|"
			f"{data.get('udf2', '')}|{data.get('udf1', '')}|{data.get('email', '')}|"
			f"{data.get('firstname', '')}|{data.get('productinfo', '')}|"
			f"{data.get('amount', '')}|{data.get('txnid', '')}|{self.merchant_key}"
		)
		calculated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
		return calculated_hash.lower() == data.get('hash', '').lower()
	
	def create_payment_request(self, invoice_id: str) -> dict:
		"""
		Create payment request for an invoice
		
		Args:
			invoice_id (str): AI Invoice ID
			
		Returns:
			dict: Payment request details including hash and form data
		"""
		try:
			invoice = frappe.get_doc("AI Invoice", invoice_id)
			subscription = frappe.get_doc("AI Subscription", invoice.subscription) if invoice.subscription else None
			user = frappe.get_doc("User", invoice.customer)
			
			# Generate unique transaction ID
			txnid = f"ORO{invoice.name.replace('-', '')}"
			
			# Prepare payment data
			payment_data = {
				"key": self.merchant_key,
				"txnid": txnid,
				"amount": str(float(invoice.total_amount)),
				"productinfo": f"{invoice.plan} Subscription" if invoice.plan else "Oropendola AI Service",
				"firstname": user.first_name or user.email.split('@')[0],
				"email": user.email,
				"phone": user.mobile_no or user.phone or "9999999999",
				"surl": f"{frappe.utils.get_url()}/api/method/oropendola_ai.oropendola_ai.api.payment.payu_success",
				"furl": f"{frappe.utils.get_url()}/api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure",
				"udf1": invoice.name,  # Store invoice ID
				"udf2": invoice.subscription or "",
				"udf3": invoice.plan or "",
				"udf4": "",
				"udf5": ""
			}
			
			# Generate hash
			payment_data["hash"] = self.generate_hash(payment_data)
			
			# Update invoice with transaction ID
			invoice.db_set("payment_gateway_order_id", txnid, update_modified=False)
			invoice.db_set("payment_gateway", "PayU", update_modified=False)
			frappe.db.commit()
			
			return {
				"success": True,
				"payment_url": f"{self.base_url}/_payment",
				"payment_data": payment_data,
				"txnid": txnid,
				"invoice_id": invoice.name
			}
			
		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Payment Request Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def verify_payment(self, response_data: dict) -> dict:
		"""
		Verify payment response from PayU
		
		Args:
			response_data (dict): Response data from PayU
			
		Returns:
			dict: Verification result
		"""
		try:
			# Verify hash
			if not self.verify_hash(response_data):
				return {
					"success": False,
					"error": "Invalid payment hash"
				}
			
			# Check payment status
			status = response_data.get("status")
			if status == "success":
				return {
					"success": True,
					"status": "success",
					"payment_id": response_data.get("mihpayid"),
					"txnid": response_data.get("txnid"),
					"amount": response_data.get("amount"),
					"payment_mode": response_data.get("mode")
				}
			else:
				return {
					"success": False,
					"status": status,
					"error": response_data.get("error_Message", "Payment failed")
				}
				
		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Payment Verification Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def process_payment_success(self, response_data: dict) -> dict:
		"""
		Process successful payment and activate subscription
		
		Args:
			response_data (dict): Response data from PayU
			
		Returns:
			dict: Processing result
		"""
		try:
			# Verify payment
			verification = self.verify_payment(response_data)
			
			if not verification["success"]:
				return verification
			
			# Get invoice ID from udf1
			invoice_id = response_data.get("udf1")
			if not invoice_id:
				return {
					"success": False,
					"error": "Invoice ID not found in payment response"
				}
			
			# Get invoice
			invoice = frappe.get_doc("AI Invoice", invoice_id)
			
			# Update invoice with payment details
			invoice.db_set("payment_gateway_payment_id", response_data.get("mihpayid"), update_modified=False)
			invoice.db_set("payment_gateway_response", json.dumps(response_data), update_modified=False)
			invoice.db_set("status", "Paid", update_modified=False)
			invoice.db_set("paid_date", frappe.utils.now(), update_modified=False)
			invoice.db_set("amount_paid", float(response_data.get("amount", 0)), update_modified=False)
			invoice.db_set("payment_method", response_data.get("mode", ""), update_modified=False)
			
			# Update Payment Session if exists
			try:
				from oropendola_ai.oropendola_ai.doctype.payment_session.payment_session import PaymentSession
				session = PaymentSession.get_active_session(invoice_id)
				if session:
					session.mark_as_success(
						transaction_id=response_data.get("mihpayid"),
						gateway_response=response_data
					)
					frappe.logger().info(f"Payment session {session.name} marked as success")
			except Exception as session_error:
				frappe.log_error(message=str(session_error), title="Payment Session Update Error")
				# Continue even if session update fails

			# Update subscription using centralized renewal logic
			if invoice.subscription:
				from oropendola_ai.oropendola_ai.api.subscription_renewal import apply_payment_to_subscription
				apply_payment_to_subscription(invoice.name)

			frappe.db.commit()

			frappe.logger().info(f"Payment successful for invoice {invoice.name}")
			
			return {
				"success": True,
				"invoice_id": invoice.name,
				"subscription_id": invoice.subscription,
				"amount": response_data.get("amount"),
				"payment_id": response_data.get("mihpayid")
			}
			
		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Payment Processing Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def process_payment_failure(self, response_data: dict) -> dict:
		"""
		Process failed payment
		
		Args:
			response_data (dict): Response data from PayU
			
		Returns:
			dict: Processing result
		"""
		try:
			# Get invoice ID
			invoice_id = response_data.get("udf1")
			if invoice_id:
				invoice = frappe.get_doc("AI Invoice", invoice_id)
				invoice.db_set("status", "Failed", update_modified=False)
				invoice.db_set("payment_gateway_response", json.dumps(response_data), update_modified=False)

				# Update Payment Session if exists
				try:
					from oropendola_ai.oropendola_ai.doctype.payment_session.payment_session import PaymentSession
					session = PaymentSession.get_active_session(invoice_id)
					if session:
						session.mark_as_failed(
							error_message=response_data.get("error_Message", "Payment failed"),
							gateway_response=response_data
						)
						frappe.logger().info(f"Payment session {session.name} marked as failed")
				except Exception as session_error:
					frappe.log_error(message=str(session_error), title="Payment Session Update Error")
					# Continue even if session update fails

				frappe.db.commit()

			return {
				"success": False,
				"error": response_data.get("error_Message", "Payment failed"),
				"invoice_id": invoice_id
			}

		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Payment Failure Processing Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def check_payment_status(self, txnid: str) -> dict:
		"""
		Check payment status using Verify Payment API
		
		Args:
			txnid (str): Transaction ID
			
		Returns:
			dict: Payment status
		"""
		try:
			# Prepare verify command
			command = "verify_payment"
			hash_string = f"{self.merchant_key}|{command}|{txnid}|{self.merchant_salt}"
			hash_value = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
			
			# API endpoint
			url = f"{self.base_url}/merchant/postservice.php?form=2"
			
			# Prepare data
			data = {
				"key": self.merchant_key,
				"command": command,
				"hash": hash_value,
				"var1": txnid
			}
			
			# Make request
			response = requests.post(url, data=data)
			result = response.json()
			
			return {
				"success": True,
				"status": result.get("status"),
				"transaction_details": result.get("transaction_details", [])
			}
			
		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Status Check Error")
			return {
				"success": False,
				"error": str(e)
			}

	def create_bolt_payment_request(self, invoice_id: str, embed_mode: bool = False) -> dict:
		"""
		Create payment request with PayU Bolt (embedded checkout)
		Bolt allows embedding payment page in iframe

		Args:
			invoice_id (str): AI Invoice ID
			embed_mode (bool): If True, returns params for Bolt embedded mode

		Returns:
			dict: Payment request with Bolt configuration
		"""
		try:
			# Get base payment request
			base_request = self.create_payment_request(invoice_id)

			if not base_request.get("success"):
				return base_request

			# Add Bolt-specific parameters
			payment_data = base_request["payment_data"]

			# PayU Bolt customization options
			bolt_config = {
				"key": self.merchant_key,
				"txnid": payment_data["txnid"],
				"amount": payment_data["amount"],
				"productinfo": payment_data["productinfo"],
				"firstname": payment_data["firstname"],
				"email": payment_data["email"],
				"phone": payment_data["phone"],
				"surl": payment_data["surl"],
				"furl": payment_data["furl"],
				"hash": payment_data["hash"],
				"udf1": payment_data["udf1"],
				"udf2": payment_data["udf2"],
				"udf3": payment_data["udf3"],

				# Bolt customization parameters (per PayU docs)
				"enforce_paymethod": "",  # Can specify specific payment method
				"display_lang": "EN",  # EN/HI/TE/TA/MR/GU
				"pg_redirect_flow": "embedded" if embed_mode else "inline",  # embedded for iframe
				"show_payment_mode": "CC,DC,NB,UPI,CASH",  # Show all payment modes
			}

			return {
				"success": True,
				"mode": "bolt_embedded" if embed_mode else "bolt_inline",
				"payu_mode": self.mode,  # test or production
				"bolt_config": bolt_config,
				"merchant_key": self.merchant_key,
				"invoice_id": invoice_id,
				"embed_mode": embed_mode,
				"instructions": {
					"embedded": "Use PayU Bolt SDK on frontend with these parameters in iframe",
					"inline": "Redirect user to PayU with these parameters"
				}
			}

		except Exception as e:
			frappe.log_error(message=str(e), title="PayU Bolt Request Error")
			return {
				"success": False,
				"error": str(e)
			}


# Singleton gateway instance
_gateway = None

def get_gateway():
	"""Get singleton PayUGateway instance"""
	global _gateway
	if _gateway is None:
		_gateway = PayUGateway()
	return _gateway


@frappe.whitelist(allow_guest=False)
def create_payment_request(invoice_id: str):
	"""
	Create PayU payment request for an invoice
	
	Args:
		invoice_id (str): Invoice ID
		
	Returns:
		dict: Payment request details
	"""
	gateway = get_gateway()
	return gateway.create_payment_request(invoice_id)


@frappe.whitelist(allow_guest=False)
def check_payment_status(txnid: str):
	"""
	Check payment status
	
	Args:
		txnid (str): Transaction ID
		
	Returns:
		dict: Payment status
	"""
	gateway = get_gateway()
	return gateway.check_payment_status(txnid)


# Whitelist Bolt API
@frappe.whitelist(allow_guest=False)
def create_bolt_payment(invoice_id: str, embed_mode: bool = False):
	"""
	Create PayU Bolt payment request (can be embedded)
	
	Args:
		invoice_id (str): Invoice ID
		embed_mode (bool): Enable embedded mode for iframe
		
	Returns:
		dict: Bolt payment configuration
	"""
	gateway = get_gateway()
	return gateway.create_bolt_payment_request(invoice_id, embed_mode)
