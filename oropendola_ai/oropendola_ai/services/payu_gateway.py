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
		"""Initialize PayU gateway with credentials from site config"""
		# Get credentials from site config
		self.merchant_key = frappe.conf.get("payu_merchant_key")
		self.merchant_salt = frappe.conf.get("payu_merchant_salt")
		self.mode = frappe.conf.get("payu_mode", "test")
		
		if not all([self.merchant_key, self.merchant_salt]):
			frappe.throw("PayU credentials not configured. Please add payu_merchant_key and payu_merchant_salt to site_config.json")
		
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
			user = frappe.get_doc("User", invoice.user)
			
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
			
			# Update subscription
			if invoice.subscription:
				subscription = frappe.get_doc("AI Subscription", invoice.subscription)
				subscription.db_set("status", "Active", update_modified=False)
				subscription.db_set("amount_paid", float(response_data.get("amount", 0)), update_modified=False)
				subscription.db_set("last_payment_date", frappe.utils.now(), update_modified=False)
			
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
