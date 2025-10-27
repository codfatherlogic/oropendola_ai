# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_days, getdate


class AIInvoice(Document):
	"""
	AI Invoice DocType for billing management.
	Handles invoice generation, payment tracking, and reconciliation.
	"""
	
	def before_insert(self):
		"""Set defaults before insert"""
		if not self.invoice_date:
			self.invoice_date = today()
		
		if not self.due_date and self.invoice_date:
			self.due_date = add_days(self.invoice_date, 7)  # 7 days payment term
	
	def validate(self):
		"""Validate invoice"""
		self.validate_amounts()
		self.calculate_total()
		self.validate_dates()
	
	def validate_amounts(self):
		"""Ensure amounts are valid"""
		if self.amount_due < 0:
			frappe.throw("Amount due cannot be negative")
		
		if self.amount_paid and self.amount_paid > self.amount_due:
			frappe.throw("Amount paid cannot exceed amount due")
	
	def calculate_total(self):
		"""Calculate total amount"""
		total = self.amount_due or 0
		total += self.tax_amount or 0
		total -= self.discount_amount or 0
		self.total_amount = total
	
	def validate_dates(self):
		"""Validate invoice dates"""
		if self.due_date and getdate(self.invoice_date) > getdate(self.due_date):
			frappe.throw("Invoice date cannot be after due date")
		
		if self.period_start and self.period_end:
			if getdate(self.period_start) > getdate(self.period_end):
				frappe.throw("Period start cannot be after period end")
	
	def mark_as_paid(self, payment_id=None, payment_method=None, receipt_url=None):
		"""Mark invoice as paid"""
		self.status = "Paid"
		self.amount_paid = self.total_amount
		self.paid_date = today()
		
		if payment_id:
			self.payment_gateway_payment_id = payment_id
		if payment_method:
			self.payment_method = payment_method
		if receipt_url:
			self.payment_receipt_url = receipt_url
		
		self.save(ignore_permissions=True)
		
		# Update subscription payment info
		if self.subscription:
			subscription = frappe.get_doc("AI Subscription", self.subscription)
			subscription.amount_paid = (subscription.amount_paid or 0) + self.total_amount
			subscription.last_payment_date = today()
			subscription.status = "Active"
			subscription.save(ignore_permissions=True)
	
	def mark_as_failed(self, reason=None):
		"""Mark invoice as failed"""
		self.status = "Failed"
		if reason:
			self.admin_notes = f"Payment failed: {reason}"
		self.save(ignore_permissions=True)
		
		# Update subscription status
		if self.subscription:
			subscription = frappe.get_doc("AI Subscription", self.subscription)
			subscription.status = "Past Due"
			subscription.save(ignore_permissions=True)
	
	@staticmethod
	def create_subscription_invoice(subscription_name):
		"""Create invoice for a subscription"""
		subscription = frappe.get_doc("AI Subscription", subscription_name)
		plan = frappe.get_doc("AI Plan", subscription.plan)
		
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": subscription.customer,
			"subscription": subscription_name,
			"plan": subscription.plan,
			"status": "Pending",
			"invoice_date": today(),
			"due_date": add_days(today(), 7),
			"period_start": subscription.start_date,
			"period_end": subscription.end_date,
			"billing_type": "Subscription",
			"amount_due": plan.price,
			"base_plan_amount": plan.price,
			"currency": plan.currency,
			"payment_gateway": "Razorpay",
			"total_requests": 0,
			"total_usage_units": 0,
			"overage_units": 0,
			"overage_amount": 0
		})
		
		invoice.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return invoice
	
	@staticmethod
	def create_usage_invoice(subscription_name, usage_summary):
		"""Create invoice based on usage (for metered billing)"""
		subscription = frappe.get_doc("AI Subscription", subscription_name)
		plan = frappe.get_doc("AI Plan", subscription.plan)
		
		# Calculate overage if applicable
		overage_units = 0
		overage_amount = 0
		
		if plan.requests_limit_per_day > 0:  # Metered plan
			total_allowed = plan.requests_limit_per_day * plan.duration_days
			if usage_summary.get("total_requests", 0) > total_allowed:
				overage_units = usage_summary["total_requests"] - total_allowed
				# Charge ₹0.5 per overage request (configurable)
				overage_amount = overage_units * 0.5
		
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": subscription.customer,
			"subscription": subscription_name,
			"plan": subscription.plan,
			"status": "Pending",
			"invoice_date": today(),
			"billing_type": "Usage",
			"amount_due": plan.price + overage_amount,
			"base_plan_amount": plan.price,
			"overage_amount": overage_amount,
			"currency": plan.currency,
			"payment_gateway": "Razorpay",
			"total_requests": usage_summary.get("total_requests", 0),
			"total_usage_units": usage_summary.get("total_cost_units", 0),
			"overage_units": overage_units
		})
		
		invoice.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return invoice
