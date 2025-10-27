# Copyright (c) 2025, sammish.thundiyil@gmail.com and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestAIPlan(FrappeTestCase):
	"""Test cases for AI Plan DocType"""
	
	def setUp(self):
		"""Setup test data"""
		self.cleanup_test_plans()
	
	def tearDown(self):
		"""Cleanup after tests"""
		self.cleanup_test_plans()
	
	def cleanup_test_plans(self):
		"""Remove test plans"""
		frappe.db.delete("AI Plan", {"plan_id": ["like", "TEST_%"]})
		frappe.db.commit()
	
	def test_create_trial_plan(self):
		"""Test creating a trial plan"""
		plan = frappe.get_doc({
			"doctype": "AI Plan",
			"plan_id": "TEST_TRIAL",
			"title": "Test Trial Plan",
			"description": "Test trial plan for 1 day",
			"price": 199,
			"currency": "INR",
			"duration_days": 1,
			"requests_limit_per_day": 200,
			"rate_limit_qps": 10,
			"priority_score": 10,
			"is_trial": 1,
			"is_active": 1,
			"support_level": "Standard"
		})
		plan.insert()
		
		self.assertEqual(plan.plan_id, "TEST_TRIAL")
		self.assertTrue(plan.is_trial)
		self.assertEqual(plan.get_daily_quota(), 200)
		self.assertFalse(plan.is_unlimited())
	
	def test_create_unlimited_plan(self):
		"""Test creating an unlimited plan"""
		plan = frappe.get_doc({
			"doctype": "AI Plan",
			"plan_id": "TEST_UNLIMITED",
			"title": "Test Unlimited Plan",
			"description": "Test unlimited plan",
			"price": 4999,
			"currency": "INR",
			"duration_days": 30,
			"requests_limit_per_day": -1,
			"rate_limit_qps": 0,
			"priority_score": 50,
			"is_trial": 0,
			"is_active": 1,
			"support_level": "Enterprise"
		})
		plan.insert()
		
		self.assertTrue(plan.is_unlimited())
		self.assertIsNone(plan.get_daily_quota())
	
	def test_negative_price_validation(self):
		"""Test that negative price throws error"""
		plan = frappe.get_doc({
			"doctype": "AI Plan",
			"plan_id": "TEST_INVALID",
			"title": "Invalid Plan",
			"price": -100,
			"duration_days": 30,
			"requests_limit_per_day": 1000,
			"priority_score": 10
		})
		
		with self.assertRaises(frappe.ValidationError):
			plan.insert()
	
	def test_priority_score_validation(self):
		"""Test priority score bounds"""
		# Test negative priority
		plan = frappe.get_doc({
			"doctype": "AI Plan",
			"plan_id": "TEST_NEG_PRIORITY",
			"title": "Negative Priority",
			"price": 100,
			"duration_days": 30,
			"requests_limit_per_day": 1000,
			"priority_score": -5
		})
		
		with self.assertRaises(frappe.ValidationError):
			plan.insert()
		
		# Test priority > 100
		plan2 = frappe.get_doc({
			"doctype": "AI Plan",
			"plan_id": "TEST_HIGH_PRIORITY",
			"title": "High Priority",
			"price": 100,
			"duration_days": 30,
			"requests_limit_per_day": 1000,
			"priority_score": 150
		})
		
		with self.assertRaises(frappe.ValidationError):
			plan2.insert()
