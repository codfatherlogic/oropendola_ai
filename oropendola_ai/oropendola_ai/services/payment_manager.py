# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Payment Gateway Manager
Unified interface for multiple payment gateways (Razorpay, PayU)
Automatically selects gateway based on configuration and provides fallback.
"""

import frappe
import os
from typing import Dict, Optional


class PaymentGatewayManager:
	"""
	Manages multiple payment gateways.
	Provides a unified interface and automatic gateway selection.
	"""
	
	def __init__(self):
		self.default_gateway = os.getenv("DEFAULT_PAYMENT_GATEWAY", "razorpay").lower()
		self.enabled_gateways = self._get_enabled_gateways()
	
	def _get_enabled_gateways(self) -> list:
		"""Get list of enabled payment gateways"""
		enabled = []
		
		# Check Razorpay
		if os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET"):
			enabled.append("razorpay")
		
		# Check PayU
		if os.getenv("PAYU_MERCHANT_KEY") and os.getenv("PAYU_MERCHANT_SALT"):
			enabled.append("payu")
		
		return enabled
	
	def get_gateway(self, gateway_name: Optional[str] = None):
		"""
		Get payment gateway instance.
		
		Args:
			gateway_name (str, optional): Gateway name (razorpay/payu)
			
		Returns:
			Gateway instance
		"""
		gateway_name = gateway_name or self.default_gateway
		
		if gateway_name == "razorpay":
			from oropendola_ai.oropendola_ai.services.razorpay_gateway import get_gateway
			return get_gateway()
		elif gateway_name == "payu":
			from oropendola_ai.oropendola_ai.services.payu_gateway import get_payu_gateway
			return get_payu_gateway()
		else:
			frappe.throw(f"Unknown payment gateway: {gateway_name}")
	
	def create_payment(self, invoice_id: str, gateway: Optional[str] = None) -> Dict:
		"""
		Create payment order/request.
		
		Args:
			invoice_id (str): Invoice ID
			gateway (str, optional): Preferred gateway
			
		Returns:
			dict: Payment data
		"""
		try:
			gateway_name = gateway or self.default_gateway
			
			if gateway_name not in self.enabled_gateways:
				# Fallback to first available gateway
				if self.enabled_gateways:
					gateway_name = self.enabled_gateways[0]
					frappe.logger().warning(
						f"Gateway {gateway} not available, using {gateway_name}"
					)
				else:
					frappe.throw("No payment gateways configured")
			
			gateway_instance = self.get_gateway(gateway_name)
			
			if gateway_name == "razorpay":
				result = gateway_instance.create_order(invoice_id)
			elif gateway_name == "payu":
				result = gateway_instance.create_payment_request(invoice_id)
			
			result["gateway"] = gateway_name
			return result
			
		except Exception as e:
			frappe.log_error(f"Failed to create payment: {str(e)}", "Payment Gateway Error")
			return {
				"success": False,
				"error": str(e)
			}
	
	def get_available_gateways(self) -> Dict:
		"""
		Get list of available payment gateways.
		
		Returns:
			dict: Available gateways with their details
		"""
		gateways = {}
		
		if "razorpay" in self.enabled_gateways:
			gateways["razorpay"] = {
				"name": "Razorpay",
				"description": "Credit/Debit Cards, UPI, Net Banking, Wallets",
				"icon": "razorpay-icon.svg",
				"supported_methods": ["card", "upi", "netbanking", "wallet"]
			}
		
		if "payu" in self.enabled_gateways:
			gateways["payu"] = {
				"name": "PayU",
				"description": "Credit/Debit Cards, UPI, Net Banking, EMI",
				"icon": "payu-icon.svg",
				"supported_methods": ["card", "upi", "netbanking", "emi", "wallet"]
			}
		
		return {
			"success": True,
			"default_gateway": self.default_gateway,
			"gateways": gateways
		}


# Singleton manager instance
_payment_manager = None

def get_payment_manager():
	"""Get singleton PaymentGatewayManager instance"""
	global _payment_manager
	if _payment_manager is None:
		_payment_manager = PaymentGatewayManager()
	return _payment_manager


@frappe.whitelist(allow_guest=False)
def create_payment_order(invoice_id: str, gateway: Optional[str] = None):
	"""
	Create payment order for an invoice.
	
	Args:
		invoice_id (str): Invoice ID
		gateway (str, optional): Payment gateway (razorpay/payu)
		
	Returns:
		dict: Payment order details
	"""
	manager = get_payment_manager()
	return manager.create_payment(invoice_id, gateway)


@frappe.whitelist(allow_guest=False)
def get_payment_gateways():
	"""
	Get available payment gateways.
	
	Returns:
		dict: Available gateways
	"""
	manager = get_payment_manager()
	return manager.get_available_gateways()


@frappe.whitelist(allow_guest=False)
def get_invoice_payment_link(invoice_id: str, gateway: Optional[str] = None):
	"""
	Generate payment link for an invoice.
	
	Args:
		invoice_id (str): Invoice ID
		gateway (str, optional): Payment gateway
		
	Returns:
		dict: Payment link details
	"""
	try:
		invoice = frappe.get_doc("AI Invoice", invoice_id)
		
		# Check permissions
		if invoice.customer != frappe.db.get_value("Customer", {"email": frappe.session.user}):
			if not frappe.has_permission("AI Invoice", "read", invoice_id):
				frappe.throw("Insufficient permissions")
		
		# Check if already paid
		if invoice.status == "Paid":
			return {
				"success": False,
				"error": "Invoice already paid"
			}
		
		# Create payment
		manager = get_payment_manager()
		payment_result = manager.create_payment(invoice_id, gateway)
		
		if payment_result.get("success"):
			gateway_used = payment_result.get("gateway")
			
			if gateway_used == "razorpay":
				return {
					"success": True,
					"gateway": "razorpay",
					"order_id": payment_result.get("order_id"),
					"amount": payment_result.get("amount"),
					"currency": payment_result.get("currency"),
					"key_id": payment_result.get("key_id"),
					"checkout_url": None  # Razorpay uses inline checkout
				}
			elif gateway_used == "payu":
				return {
					"success": True,
					"gateway": "payu",
					"payment_url": payment_result.get("payment_url"),
					"payment_data": payment_result.get("payment_data"),
					"txnid": payment_result.get("txnid")
				}
		
		return payment_result
		
	except Exception as e:
		frappe.log_error(f"Failed to generate payment link: {str(e)}", "Payment Link Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def retry_failed_payment(invoice_id: str):
	"""
	Retry payment for a failed invoice.
	
	Args:
		invoice_id (str): Invoice ID
		
	Returns:
		dict: New payment link
	"""
	try:
		invoice = frappe.get_doc("AI Invoice", invoice_id)
		
		# Check permissions
		if not frappe.has_permission("AI Invoice", "write", invoice_id):
			frappe.throw("Insufficient permissions")
		
		# Check if eligible for retry
		if invoice.status not in ["Failed", "Pending"]:
			frappe.throw(f"Cannot retry payment for invoice with status: {invoice.status}")
		
		# Reset invoice status
		invoice.status = "Draft"
		invoice.save(ignore_permissions=True)
		frappe.db.commit()
		
		# Create new payment
		return get_invoice_payment_link(invoice_id)
		
	except Exception as e:
		frappe.log_error(f"Failed to retry payment: {str(e)}", "Payment Retry Error")
		return {
			"success": False,
			"error": str(e)
		}
