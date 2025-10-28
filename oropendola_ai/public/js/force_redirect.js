// Force redirect for website users trying to access desk
(function() {
    // Check if we're on the desk/app page
    if (window.location.pathname.startsWith('/app') || window.location.pathname.startsWith('/desk')) {
        // Check if user is logged in
        frappe.ready(function() {
            frappe.call({
                method: 'frappe.auth.get_logged_user',
                callback: function(r) {
                    if (r.message && r.message !== 'Guest') {
                        // User is logged in, check if they have desk access
                        frappe.call({
                            method: 'frappe.core.doctype.user.user.has_role',
                            args: {
                                role: 'System Manager'
                            },
                            callback: function(r2) {
                                if (!r2.message) {
                                    // User doesn't have System Manager role
                                    // Redirect to profile dashboard
                                    console.log('Redirecting website user to profile dashboard');
                                    window.location.replace('/my-profile');
                                }
                            }
                        });
                    }
                }
            });
        });
    }
})();
