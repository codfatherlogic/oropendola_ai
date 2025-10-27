# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
PayU Payment Gateway Integration
Handles payment processing, webhooks, and invoice reconciliation for PayU India.
"""

import frappe
import os
import hashlib
import json
from typing import Dict, Optional


class PayUGateway:
	"""
	PayU payment gateway integration for India.
	Handles payment form generation, verification, and webhooks.
	"""
	
	def __init__(self):
		self.merchant_key = os.getenv("PAYU_MERCHANT_KEY")
		self.merchant_salt = os.getenv("PAYU_MERCHANT_SALT")
		self.mode = os.getenv("PAYU_MODE", "test")  # test or live
		
		if not all([self.merchant_key, self.merchant_salt]):
			frappe.throw("PayU credentials not configured in environment")
		
		# Set base URL based on mode
		if self.mode == "live":
			self.base_url = "https://secure.payu.in"
		else:
			self.base_url = "https://test.payu.in"
	
	def generate_hash(self, data: Dict) -> str:
		"""
		Generate PayU hash for payment request.
		
		Hash formula: sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||salt)
		
		Args:
			data (dict): Payment data
			
		Returns:
			str: Generated hash
		"""
		hash_string = (
			f"{self.merchant_key}|{data['txnid']}|{data['amount']}|"
			f"{data['productinfo']}|{data['firstname']}|{data['email']}|"
			f"{data.get('udf1', '')}|{data.get('udf2', '')}|{data.get('udf3', '')}|"
			f"{data.get('udf4', '')}|{data.get('udf5', '')}||||||{self.merchant_salt}"
		)
		
		return hashlib.sha512(hash_string.encode()).hexdigest()
	
	def verify_hash(self, response_data: Dict) -> bool:
		"""
		Verify PayU response hash.
		
		Hash formula for response: sha512(salt|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)
		
		Args:
			response_data (dict): Response data from PayU
			
		Returns:
			bool: True if hash is valid
		"""
		received_hash = response_data.get('hash', '')
		
		# Build hash string (reverse order for response)
		hash_string = (
			f"{self.merchant_salt}|{response_data.get('status', '')}|"
			f"||||||{response_data.get('udf5', '')}|{response_data.get('udf4', '')}|"
			f"{response_data.get('udf3', '')}|{response_data.get('udf2', '')}|"
			f"{response_data.get('udf1', '')}|{response_data.get('email', '')}|"
			f"{response_data.get('firstname', '')}|{response_data.get('productinfo', '')}|"
			f"{response_data.get('amount', '')}|{response_data.get('txnid', '')}|"
			f"{self.merchant_key}"
		)
		
		calculated_hash = hashlib.sha512(hash_string.encode()).hexdigest()
		
		return received_hash == calculated_hash
	
	def create_payment_request(self, invoice_id: str) -> Dict:
		"""
		Create payment request for an invoice.
		
		Args:
			invoice_id (str): AI Invoice ID
			
		Returns:
			dict: Payment form data
		"""
		try:
			invoice = frappe.get_doc("AI Invoice", invoice_id)
			customer = frappe.get_doc("Customer", invoice.customer)
			
			# Generate unique transaction ID
			txnid = f"TXN-{invoice.name}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"
			
			# Get customer details
			customer_email = invoice.billing_email or customer.email_id or "customer@example.com"
			customer_name = customer.customer_name or "Customer"
			customer_phone = customer.mobile_no or customer.phone or "9999999999"
			
			# Prepare payment data
			payment_data = {
				"key": self.merchant_key,
				"txnid": txnid,
				"amount": f"{invoice.total_amount:.2f}",
				"productinfo": f"AI Subscription - {invoice.plan or 'Premium'}",
				"firstname": customer_name.split()[0],
				"email": customer_email,
				"phone": customer_phone,
				"surl": f"{frappe.utils.get_url()}/api/method/oropendola_ai.services.payu_gateway.payment_success",
				"furl": f"{frappe.utils.get_url()}/api/method/oropendola_ai.services.payu_gateway.payment_failure",
				"udf1": invoice_id,  # Store invoice ID
				"udf2": invoice.subscription or "",
				"udf3": "",
				"udf4": "",
				"udf5": "",
			}
			
			# Generate hash
			payment_data["hash"] = self.generate_hash(payment_data)
			
			# Update invoice with transaction details
			invoice.payment_gateway = "PayU"
			invoice.payment_gateway_order_id = txnid
			invoice.status = "Pending"
			invoice.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"payment_url": f"{self.base_url}/_payment",
				"payment_data": payment_data,
				"txnid": txnid
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to create PayU payment request: {str(e)}", "PayU Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def process_payment_response(self, response_data: Dict) -> Dict:
		"""
		Process payment response from PayU.
		
		Args:
			response_data (dict): Response data from PayU
			
		Returns:
			dict: Processing result
		"""
		try:
			# Verify hash
			if not self.verify_hash(response_data):
				frappe.log_error("Invalid PayU hash", "PayU Verification Error")
				return {
					"success": False,
					"error": "Invalid payment signature"
				}
			
			# Get invoice from UDF1
			invoice_id = response_data.get("udf1")
			if not invoice_id:
				return {
					"success": False,
					"error": "Invoice ID not found in response"
				}
			
			invoice = frappe.get_doc("AI Invoice", invoice_id)
			
			# Get payment status
			status = response_data.get("status", "").lower()
			payment_id = response_data.get("mihpayid")  # PayU payment ID
			txnid = response_data.get("txnid")
			
			if status == "success":
				# Payment successful
				payment_method = response_data.get("mode", "").replace("_", " ").title()
				
				invoice.mark_as_paid(
					payment_id=payment_id,
					payment_method=payment_method,
					receipt_url=f"{self.base_url}/transaction/{payment_id}"
				)
				
				return {
					"success": True,
					"invoice_id": invoice.name,
					"payment_id": payment_id,
					"status": "Paid",
					"message": "Payment successful"
				}
			
			elif status == "failure":
				# Payment failed
				error_message = response_data.get("error_Message", "Payment failed")
				invoice.mark_as_failed(reason=error_message)
				
				return {
					"success": False,
					"invoice_id": invoice.name,
					"status": "Failed",
					"error": error_message
				}
			
			elif status == "pending":
				# Payment pending
				invoice.status = "Pending"
				invoice.admin_notes = f"Payment pending: {response_data.get('bank_ref_num', 'N/A')}"
				invoice.save(ignore_permissions=True)
				frappe.db.commit()
				
				return {
					"success": True,
					"invoice_id": invoice.name,
					"status": "Pending",
					"message": "Payment is being processed"
				}
			
			else:
				return {
					"success": False,
					"error": f"Unknown payment status: {status}"
				}
			
		except Exception as e:
			frappe.log_error(f"Failed to process PayU response: {str(e)}", "PayU Processing Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def verify_payment(self, txnid: str) -> Dict:
		"""
		Verify payment status with PayU API.
		
		Args:
			txnid (str): Transaction ID
			
		Returns:
			dict: Payment status
		"""
		try:
			import requests
			
			# Generate verification hash
			command = "verify_payment"
			hash_string = f"{self.merchant_key}|{command}|{txnid}|{self.merchant_salt}"
			hash_value = hashlib.sha512(hash_string.encode()).hexdigest()
			
			# API request
			verify_url = f"{self.base_url}/merchant/postservice.php?form=2"
			
			data = {
				"key": self.merchant_key,
				"command": command,
				"var1": txnid,
				"hash": hash_value
			}
			
			response = requests.post(verify_url, data=data)
			result = response.json()
			
			return {
				"success": True,
				"status": result.get("status"),
				"transaction_details": result.get("transaction_details", {})
			}
			
		except Exception as e:
			frappe.log_error(f"Failed to verify PayU payment: {str(e)}", "PayU Verify Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def refund_payment(self, payment_id: str, amount: float, invoice_id: str) -> Dict:
		"""
		Initiate refund for a payment.
		
		Args:
			payment_id (str): PayU payment ID (mihpayid)
			amount (float): Refund amount
			invoice_id (str): Invoice ID
			
		Returns:
			dict: Refund result
		"""
		try:
			import requests
			
			# Generate refund hash
			command = "cancel_refund_transaction"
			refund_amount = f"{amount:.2f}"
			
			hash_string = f"{self.merchant_key}|{command}|{payment_id}|{self.merchant_salt}"
			hash_value = hashlib.sha512(hash_string.encode()).hexdigest()
			
			# API request
			refund_url = f"{self.base_url}/merchant/postservice.php?form=2"
			
			data = {
				"key": self.merchant_key,
				"command": command,
				"var1": payment_id,
				"var2": refund_amount,
				"hash": hash_value
			}
			
			response = requests.post(refund_url, data=data)
			result = response.json()
			
			if result.get("status") == 1:
				# Update invoice
				invoice = frappe.get_doc("AI Invoice", invoice_id)
				invoice.status = "Refunded"
				invoice.admin_notes = f"Refund initiated: {result.get('msg', '')}"
				invoice.save(ignore_permissions=True)
				frappe.db.commit()
				
				return {
					"success": True,
					"message": result.get("msg", "Refund initiated"),
					"refund_id": result.get("request_id")
				}
			else:
				return {
					"success": False,
					"error": result.get("msg", "Refund failed")
				}
			
		except Exception as e:
			frappe.log_error(f"Failed to refund PayU payment: {str(e)}", "PayU Refund Error")
			return {
				"success": False,
				"error": str(e)
			}


# Singleton gateway instance
_payu_gateway = None

def get_payu_gateway():
	"""Get singleton PayUGateway instance"""
	global _payu_gateway
	if _payu_gateway is None:
		_payu_gateway = PayUGateway()
	return _payu_gateway


@frappe.whitelist(allow_guest=False)
def create_payment(invoice_id: str):
	"""
	Create PayU payment request for an invoice.
	
	Args:
		invoice_id (str): Invoice ID
		
	Returns:
		dict: Payment form data
	"""
	gateway = get_payu_gateway()
	return gateway.create_payment_request(invoice_id)


@frappe.whitelist(allow_guest=True)
def payment_success():
	"""
	PayU success callback endpoint.
	Handles successful payment responses.
	"""
	try:
		# Get POST data
		response_data = frappe.form_dict
		
		frappe.logger().info(f"PayU Success Callback: {json.dumps(response_data)}")
		
		gateway = get_payu_gateway()
		result = gateway.process_payment_response(dict(response_data))
		
		if result.get("success"):
			# Redirect to success page
			return frappe.respond_as_web_page(
				"Payment Successful",
				f"""
				<div style="text-align: center; padding: 40px;">
					<h1 style="color: green;">✓ Payment Successful</h1>
					<p>Your payment has been processed successfully.</p>
					<p><strong>Invoice ID:</strong> {result.get('invoice_id')}</p>
					<p><strong>Payment ID:</strong> {result.get('payment_id')}</p>
					<br>
					<a href="/app/ai-subscription" class="btn btn-primary">View Subscriptions</a>
				</div>
				""",
				http_status_code=200
			)
		else:
			return frappe.respond_as_web_page(
				"Payment Processing",
				f"""
				<div style="text-align: center; padding: 40px;">
					<h1 style="color: orange;">⚠ Payment Processing</h1>
					<p>{result.get('message', 'Payment is being processed')}</p>
					<br>
					<a href="/app/ai-invoice" class="btn btn-primary">View Invoices</a>
				</div>
				""",
				http_status_code=200
			)
		
	except Exception as e:
		frappe.log_error(f"PayU success callback failed: {str(e)}", "PayU Callback Error")
		return frappe.respond_as_web_page(
			"Error",
			f"<p>An error occurred while processing your payment: {str(e)}</p>",
			http_status_code=500
		)


@frappe.whitelist(allow_guest=True)
def payment_failure():
	"""
	PayU failure callback endpoint.
	Handles failed payment responses.
	"""
	try:
		# Get POST data
		response_data = frappe.form_dict
		
		frappe.logger().info(f"PayU Failure Callback: {json.dumps(response_data)}")
		
		gateway = get_payu_gateway()
		result = gateway.process_payment_response(dict(response_data))
		
		error_message = response_data.get("error_Message", "Payment failed")
		
		return frappe.respond_as_web_page(
			"Payment Failed",
			f"""
			<div style="text-align: center; padding: 40px;">
				<h1 style="color: red;">✗ Payment Failed</h1>
				<p><strong>Error:</strong> {error_message}</p>
				<p>Invoice ID: {result.get('invoice_id', 'N/A')}</p>
				<br>
				<a href="/app/ai-invoice" class="btn btn-primary">Retry Payment</a>
			</div>
			""",
			http_status_code=200
		)
		
	except Exception as e:
		frappe.log_error(f"PayU failure callback failed: {str(e)}", "PayU Callback Error")
		return frappe.respond_as_web_page(
			"Error",
			f"<p>An error occurred: {str(e)}</p>",
			http_status_code=500
		)


@frappe.whitelist(allow_guest=False)
def verify_transaction(txnid: str):
	"""
	Verify transaction status with PayU.
	
	Args:
		txnid (str): Transaction ID
		
	Returns:
		dict: Transaction status
	"""
	gateway = get_payu_gateway()
	return gateway.verify_payment(txnid)


@frappe.whitelist(allow_guest=False)
def initiate_refund(payment_id: str, amount: float, invoice_id: str):
	"""
	Initiate refund for a payment.
	
	Args:
		payment_id (str): PayU payment ID
		amount (float): Refund amount
		invoice_id (str): Invoice ID
		
	Returns:
		dict: Refund result
	"""
	# Check permissions
	if not frappe.has_permission("AI Invoice", "write"):
		frappe.throw("Insufficient permissions")
	
	gateway = get_payu_gateway()
	return gateway.refund_payment(payment_id, float(amount), invoice_id)
