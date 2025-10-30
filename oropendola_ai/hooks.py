app_name = "oropendola_ai"
app_title = "Oropendola Ai"
app_publisher = "sammish.thundiyil@gmail.com"
app_description = "Oropendola AI"
app_email = "sammish.thundiyil@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# Disabled - prevent 'No App' error for website users
# add_to_apps_screen = [
# 	{
# 		"name": "oropendola_ai",
# 		"logo": "/files/icon.png",
# 		"title": "Oropendola AI",
# 		"route": "/app",
# 		"has_permission": "oropendola_ai.oropendola_ai.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/oropendola_ai/css/oropendola_ai.css"
# app_include_js = "/assets/oropendola_ai/js/oropendola_ai.js"

# include js, css files in header of web template
# web_include_css = "/assets/oropendola_ai/css/oropendola_ai.css"
web_include_js = [
    "/assets/oropendola_ai/js/cache-buster.js",
    "/assets/oropendola_ai/js/security-redirect.js",
    "/assets/oropendola_ai/js/force_redirect.js"
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "oropendola_ai/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "oropendola_ai/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "index"

# Override default login page with custom dark-themed login
website_route_rules = [
	{'from_route': '/login', 'to_route': '/login'},
]

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "oropendola_ai.utils.jinja_methods",
# 	"filters": "oropendola_ai.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "oropendola_ai.install.before_install"
after_install = "oropendola_ai.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "oropendola_ai.uninstall.before_uninstall"
# after_uninstall = "oropendola_ai.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "oropendola_ai.utils.before_app_install"
# after_app_install = "oropendola_ai.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "oropendola_ai.utils.before_app_uninstall"
# after_app_uninstall = "oropendola_ai.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "oropendola_ai.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"User": {
		"after_insert": "oropendola_ai.oropendola_ai.utils.user_utils.create_default_subscription"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"oropendola_ai.oropendola_ai.tasks.reset_daily_quotas",
		"oropendola_ai.oropendola_ai.tasks.generate_billing_invoices",
		"oropendola_ai.oropendola_ai.tasks.cleanup_old_usage_logs"
	],
	"hourly": [
		"oropendola_ai.oropendola_ai.tasks.check_expired_subscriptions",
		"oropendola_ai.oropendola_ai.tasks.send_quota_alerts"
	],
	"cron": {
		"*/5 * * * *": [
			"oropendola_ai.oropendola_ai.tasks.perform_health_checks",
			"oropendola_ai.oropendola_ai.tasks.sync_redis_usage_to_db"
		]
	}
}

# Testing
# -------

# before_tests = "oropendola_ai.install.before_tests"

# Overriding Methods
# ------------------------------
# Disabled - using Frappe's default login instead
# override_whitelisted_methods = {
# 	"frappe.auth.get_logged_user": "oropendola_ai.oropendola_ai.api.auth.custom_login"
# }

# Use auth hooks to intercept login
# Disabled - causing redirect issues
# auth_hooks = [
# 	"oropendola_ai.oropendola_ai.utils.auth_hooks.validate_auth"
# ]
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "oropendola_ai.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["oropendola_ai.oropendola_ai.utils.cache_utils.set_cache_headers"]
after_request = ["oropendola_ai.oropendola_ai.utils.cache_utils.set_cache_headers"]

# Session Events
# ----------------
# Disabled - was interfering with login
# on_session_creation = "oropendola_ai.oropendola_ai.utils.session_utils.on_session_creation"

# Boot Session
# ----------------
# Disabled - was causing 'No App' error during login
# extend_bootinfo = "oropendola_ai.oropendola_ai.utils.session_utils.extend_bootinfo"

# Job Events
# ----------
# before_job = ["oropendola_ai.utils.before_job"]
# after_job = ["oropendola_ai.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"oropendola_ai.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

