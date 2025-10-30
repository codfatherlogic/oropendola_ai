# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_social_login_providers():
	"""
	Get available social login providers configured in Frappe
	Returns list of providers with their configuration for frontend integration
	"""
	try:
		# Get configured social login providers from Frappe
		social_logins = frappe.db.get_all(
			'Social Login Key',
			filters={'enable_social_login': 1},
			fields=['name', 'social_login_provider', 'provider_name', 'client_id', 'icon']
		)
		
		providers = []
		provider_config = {
			'google': {
				'name': 'Google',
				'icon': 'https://oropendola.ai/files/google.png',
				'color': '#4285F4'
			},
			'github': {
				'name': 'GitHub',
				'icon': 'https://oropendola.ai/files/github.png',
				'color': '#333333'
			},
			'facebook': {
				'name': 'Facebook',
				'icon': 'https://www.facebook.com/images/fb_icon_325x325.png',
				'color': '#1877F2'
			},
			'microsoft': {
				'name': 'Microsoft',
				'icon': 'https://c.s-microsoft.com/favicon.ico',
				'color': '#00A4EF'
			}
		}
		
		for login in social_logins:
			# Use social_login_provider field which contains the provider name
			provider = (login.social_login_provider or login.name).lower()
			if provider in provider_config:
				config = provider_config[provider].copy()
				config['provider'] = provider
				config['name'] = login.provider_name or config.get('name')
				config['enabled'] = True
				providers.append(config)
		
		return {
			'success': True,
			'providers': providers,
			'count': len(providers)
		}
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Social Login Provider Fetch Error')
		return {
			'success': False,
			'message': str(e),
			'providers': []
		}


@frappe.whitelist(allow_guest=True)
def initiate_social_login(provider, redirect_to=None):
	"""
	Initiate social login flow for a given provider
	Fetches OAuth configuration and returns the authorization URL
	
	Args:
		provider: OAuth provider name (google, github, etc.)
		redirect_to: Optional redirect path after successful login (default: /my-profile)
			- If 'pricing' or 'payment': redirect to /pricing after login
			- If None or empty: redirect to /my-profile
	"""
	try:
		provider = str(provider).lower()
		
		# Validate provider exists and is enabled
		social_login_result = frappe.db.get_value(
			'Social Login Key',
			filters={'enable_social_login': 1, 'name': provider},
			fieldname=['name', 'social_login_provider', 'client_id', 'authorize_url', 'auth_url_data'],
			as_dict=True
		)
		
		if not social_login_result:
			frappe.throw(_('Social login provider not configured'))
		
		social_login = social_login_result
		client_id = social_login.get('client_id')
		authorize_url = social_login.get('authorize_url')
		auth_url_data = social_login.get('auth_url_data', '{}')
		
		if not client_id or not authorize_url:
			frappe.throw(_('OAuth configuration incomplete for this provider'))
		
		# Build the authorization URL with provider-specific parameters
		redirect_uri = frappe.utils.get_url() + '/api/method/frappe.integrations.oauth2_logins.login_via_' + provider
		
		import json
		import hashlib
		import base64
		
		try:
			auth_params = json.loads(auth_url_data) if auth_url_data else {}
		except:
			auth_params = {}
		
		# Determine actual redirect_to value
		actual_redirect_to = None
		if redirect_to and redirect_to.lower() in ['pricing', 'payment', '/pricing']:
			actual_redirect_to = '/pricing'
		else:
			actual_redirect_to = '/my-profile'
		
		# Generate state parameter for CSRF protection with redirect_to info
		state_data = {
			'site': frappe.utils.get_url(),
			'token': frappe.generate_hash(length=32),
			'redirect_to': actual_redirect_to
		}
		state_json = json.dumps(state_data)
		state_encoded = base64.b64encode(state_json.encode()).decode()
		
		# Standard OAuth parameters
		auth_params['client_id'] = client_id
		auth_params['redirect_uri'] = redirect_uri
		auth_params['response_type'] = 'code'
		auth_params['state'] = state_encoded
		
		# Add provider-specific parameters
		if provider == 'google':
			auth_params['scope'] = auth_params.get('scope', 'https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email')
			auth_params['access_type'] = auth_params.get('access_type', 'offline')
			auth_params['prompt'] = auth_params.get('prompt', 'select_account')
		elif provider == 'github':
			auth_params['scope'] = auth_params.get('scope', 'user:email')
		elif provider == 'facebook':
			auth_params['scope'] = auth_params.get('scope', 'public_profile,email')
		elif provider == 'microsoft':
			auth_params['scope'] = auth_params.get('scope', 'user.read')
		
		# Build query string
		from urllib.parse import urlencode
		query_string = urlencode(auth_params)
		full_auth_url = f"{authorize_url}?{query_string}"
		
		frappe.logger().info(f'Social Login: Generated auth_url for {provider} with redirect_to={actual_redirect_to}: {full_auth_url}')
		
		return {
			'success': True,
			'provider': provider,
			'auth_url': full_auth_url,
			'redirect_to': actual_redirect_to
		}
	
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Social Login Initiation Error')
		return {
			'success': False,
			'message': str(e)
		}
