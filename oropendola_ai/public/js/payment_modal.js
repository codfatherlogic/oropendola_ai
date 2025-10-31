/**
 * Embedded Payment Modal
 * Handles payment gateway selection and embedded payment flows
 */

class PaymentModal {
	constructor() {
		this.currentSession = null;
		this.selectedGateway = null;
		this.invoice_id = null;
		this.onSuccess = null;
		this.onCancel = null;
	}

	/**
	 * Show payment modal
	 * @param {Object} options - Modal options
	 * @param {string} options.invoice_id - Invoice ID to pay
	 * @param {string} options.plan_name - Plan name for display
	 * @param {number} options.amount - Amount to pay
	 * @param {string} options.currency - Currency code
	 * @param {Function} options.onSuccess - Success callback
	 * @param {Function} options.onCancel - Cancel callback
	 */
	show(options) {
		this.invoice_id = options.invoice_id;
		this.onSuccess = options.onSuccess;
		this.onCancel = options.onCancel;

		// Create modal HTML
		this.createModal(options);

		// Show modal
		$('#payment-modal').modal('show');

		// Show gateway selector
		this.showGatewaySelector();
	}

	createModal(options) {
		// Remove existing modal
		$('#payment-modal').remove();

		const modalHTML = `
			<div class="modal fade" id="payment-modal" tabindex="-1" role="dialog"
				 aria-labelledby="payment-modal-title" aria-hidden="true" data-backdrop="static">
				<div class="modal-dialog modal-lg modal-dialog-centered" role="document">
					<div class="modal-content">
						<div class="modal-header">
							<h5 class="modal-title" id="payment-modal-title">Complete Your Payment</h5>
							<button type="button" class="close" data-dismiss="modal" aria-label="Close" id="modal-close-btn">
								<span aria-hidden="true">&times;</span>
							</button>
						</div>
						<div class="modal-body" id="payment-modal-body">
							<!-- Content will be dynamically loaded here -->
						</div>
						<div class="modal-footer" id="payment-modal-footer">
							<button type="button" class="btn btn-secondary" data-dismiss="modal" id="modal-cancel-btn">Cancel</button>
						</div>
					</div>
				</div>
			</div>
		`;

		$('body').append(modalHTML);

		// Store plan info
		this.planInfo = {
			name: options.plan_name,
			amount: options.amount,
			currency: options.currency
		};

		// Handle modal close
		$('#payment-modal').on('hidden.bs.modal', () => {
			this.handleModalClose();
		});

		// Handle cancel button
		$('#modal-cancel-btn').on('click', () => {
			this.cancelPayment();
		});

		// Handle X button
		$('#modal-close-btn').on('click', () => {
			this.cancelPayment();
		});
	}

	showGatewaySelector() {
		const selectorHTML = `
			<div class="gateway-selector">
				<div class="text-center mb-4">
					<h6>Select Payment Method</h6>
					<p class="text-muted">Choose your preferred payment gateway</p>
				</div>

				<div class="plan-summary mb-4 p-3 bg-light rounded">
					<div class="d-flex justify-content-between">
						<span><strong>Plan:</strong> ${this.planInfo.name}</span>
						<span><strong>${this.planInfo.currency} ${this.planInfo.amount}</strong></span>
					</div>
				</div>

				<div class="gateway-options">
					<div class="gateway-option available" data-gateway="PayU">
						<div class="gateway-card p-4 border rounded mb-3" style="cursor: pointer;">
							<div class="d-flex justify-content-between align-items-center">
								<div>
									<h6 class="mb-1">PayU <span class="badge badge-success">Active</span></h6>
									<p class="text-muted mb-0">Pay securely using PayU (embedded)</p>
								</div>
								<i class="fa fa-chevron-right"></i>
							</div>
						</div>
					</div>

					<div class="gateway-option coming-soon" data-gateway="Razorpay">
						<div class="gateway-card p-4 border rounded mb-3" style="opacity: 0.6;">
							<div class="d-flex justify-content-between align-items-center">
								<div>
									<h6 class="mb-1">Razorpay <span class="badge badge-secondary">Coming Soon</span></h6>
									<p class="text-muted mb-0">Available soon</p>
								</div>
							</div>
						</div>
					</div>

					<div class="gateway-option coming-soon" data-gateway="Stripe">
						<div class="gateway-card p-4 border rounded mb-3" style="opacity: 0.6;">
							<div class="d-flex justify-content-between align-items-center">
								<div>
									<h6 class="mb-1">Stripe <span class="badge badge-secondary">Coming Soon</span></h6>
									<p class="text-muted mb-0">Available soon</p>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		$('#payment-modal-body').html(selectorHTML);

		// Handle gateway selection
		$('.gateway-option.available .gateway-card').on('click', (e) => {
			const gateway = $(e.currentTarget).closest('.gateway-option').data('gateway');
			this.selectGateway(gateway);
		});
	}

	selectGateway(gateway) {
		this.selectedGateway = gateway;

		// Show loading
		this.showLoading('Initializing payment...');

		// Initialize payment session
		frappe.call({
			method: 'oropendola_ai.oropendola_ai.api.payment_embed.initialize_payment_session',
			args: {
				invoice_id: this.invoice_id,
				gateway: gateway,
				embed_mode: true
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					this.currentSession = r.message;
					this.loadGatewayEmbed(gateway, r.message);
				} else {
					this.showError(r.message.error || 'Failed to initialize payment');
				}
			},
			error: (err) => {
				console.error('Payment initialization error:', err);
				this.showError('Failed to initialize payment. Please try again.');
			}
		});
	}

	loadGatewayEmbed(gateway, sessionData) {
		if (gateway === 'PayU') {
			this.loadPayUBolt(sessionData);
		} else if (gateway === 'Razorpay') {
			this.showError('Razorpay integration coming soon');
		} else if (gateway === 'Stripe') {
			this.showError('Stripe integration coming soon');
		}
	}

	loadPayUBolt(sessionData) {
		const config = sessionData.gateway_config;

		if (!config || !config.bolt_config) {
			this.showError('Invalid payment configuration');
			return;
		}

		// Create PayU Bolt container
		const boltHTML = `
			<div class="payu-bolt-container">
				<div class="text-center mb-3">
					<h6>Complete Payment with PayU</h6>
					<p class="text-muted">Amount: ${config.bolt_config.currency} ${config.bolt_config.amount}</p>
				</div>
				<div id="payu-bolt-embed" class="border rounded" style="min-height: 400px;">
					<!-- PayU Bolt will load here -->
				</div>
			</div>
		`;

		$('#payment-modal-body').html(boltHTML);

		// Hide footer buttons during payment
		$('#payment-modal-footer').hide();

		// Load PayU Bolt script
		this.loadPayUScript(() => {
			this.initializePayUBolt(config.bolt_config, sessionData.session_id);
		});
	}

	loadPayUScript(callback) {
		// Check if script already loaded
		if (window.bolt) {
			callback();
			return;
		}

		// Load PayU Bolt script
		const script = document.createElement('script');
		script.src = 'https://sboxcheckout-static.citruspay.com/bolt/run/bolt.min.js';
		script.id = 'bolt';
		script.onload = callback;
		script.onerror = () => {
			this.showError('Failed to load PayU payment system. Please try again.');
		};
		document.head.appendChild(script);
	}

	initializePayUBolt(boltConfig, sessionId) {
		if (!window.bolt) {
			this.showError('PayU system not available');
			return;
		}

		// Initialize Bolt
		window.bolt.launch(boltConfig, {
			responseHandler: (response) => {
				this.handlePayUResponse(response, sessionId);
			},
			catchException: (error) => {
				console.error('PayU error:', error);
				this.showError('Payment failed. Please try again.');
				this.cancelPaymentSession(sessionId, 'PayU error: ' + error.message);
			}
		});
	}

	handlePayUResponse(response, sessionId) {
		console.log('PayU response:', response);

		// Show processing
		this.showLoading('Verifying payment...');

		// Verify payment with backend
		frappe.call({
			method: 'oropendola_ai.oropendola_ai.api.payment_embed.verify_payment_session',
			args: {
				session_id: sessionId,
				gateway_response: response
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					this.showSuccess('Payment successful! Your subscription is now active.');

					// Call success callback after delay
					setTimeout(() => {
						$('#payment-modal').modal('hide');
						if (this.onSuccess) {
							this.onSuccess(r.message);
						}
					}, 2000);
				} else {
					this.showError(r.message.error || 'Payment verification failed');
				}
			},
			error: (err) => {
				console.error('Verification error:', err);
				this.showError('Failed to verify payment. Please contact support.');
			}
		});
	}

	cancelPayment() {
		if (!this.currentSession || !this.currentSession.session_id) {
			// No active session, just close
			$('#payment-modal').modal('hide');
			if (this.onCancel) {
				this.onCancel();
			}
			return;
		}

		// Cancel active session
		this.cancelPaymentSession(this.currentSession.session_id, 'User cancelled payment');
	}

	cancelPaymentSession(sessionId, reason) {
		frappe.call({
			method: 'oropendola_ai.oropendola_ai.api.payment_embed.cancel_payment_session',
			args: {
				session_id: sessionId,
				reason: reason
			},
			callback: (r) => {
				$('#payment-modal').modal('hide');
				if (this.onCancel) {
					this.onCancel(r.message);
				}
			}
		});
	}

	handleModalClose() {
		// Cleanup
		if (this.currentSession) {
			console.log('Modal closed with active session:', this.currentSession.session_id);
		}
	}

	showLoading(message) {
		const html = `
			<div class="text-center py-5">
				<div class="spinner-border text-primary mb-3" role="status">
					<span class="sr-only">Loading...</span>
				</div>
				<p>${message}</p>
			</div>
		`;
		$('#payment-modal-body').html(html);
		$('#payment-modal-footer').hide();
	}

	showError(message) {
		const html = `
			<div class="alert alert-danger mb-0">
				<strong>Error:</strong> ${message}
			</div>
			<div class="text-center mt-3">
				<button type="button" class="btn btn-secondary" onclick="window.paymentModal.showGatewaySelector()">
					Try Again
				</button>
			</div>
		`;
		$('#payment-modal-body').html(html);
		$('#payment-modal-footer').show();
	}

	showSuccess(message) {
		const html = `
			<div class="text-center py-5">
				<i class="fa fa-check-circle text-success mb-3" style="font-size: 64px;"></i>
				<h5>${message}</h5>
			</div>
		`;
		$('#payment-modal-body').html(html);
		$('#payment-modal-footer').hide();
	}
}

// Initialize global payment modal instance
window.paymentModal = new PaymentModal();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
	module.exports = PaymentModal;
}
