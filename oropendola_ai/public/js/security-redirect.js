/**
 * Global Security Redirect Script v2.2
 * Ensures guests are redirected to login
 * Allows authenticated users full access to all pages
 * Build: 2025-01-30-UPDATED
 */

(function() {
    'use strict';
    
    // VERSION CHECK
    const SCRIPT_VERSION = '2.2-UPDATED-20250130';
    console.log('🛡️ Security Redirect Script Version:', SCRIPT_VERSION);
    
    // List of pages that require authentication
    const PROTECTED_PAGES = [
        '/my-profile',
        '/profile',
        '/me',
        '/dashboard',
        '/account'
    ];
    
    // List of pages that are always public (no auth required)
    const PUBLIC_PAGES = [
        '/login',
        '/signup',
        '/pricing',
        '/docs',
        '/'
    ];
    
    // List of admin-only pages
    const ADMIN_PAGES = [
        '/app',
        '/desk'
    ];
    
    // Get current path
    const currentPath = window.location.pathname;
    
    // Check page types
    const isPublicPage = PUBLIC_PAGES.includes(currentPath) || currentPath === '/index.html';
    const isProtectedPage = PROTECTED_PAGES.some(page => currentPath.startsWith(page));
    const isAdminPage = ADMIN_PAGES.some(page => currentPath.startsWith(page));
    
    console.log('🛡️ Security check:');
    console.log('   Current path:', currentPath);
    console.log('   Is public page:', isPublicPage);
    console.log('   Is protected page:', isProtectedPage);
    console.log('   Is admin page:', isAdminPage);
    
    // If on a truly public page (login, signup, pricing, docs), don't check auth - allow immediately
    // But homepage and protected pages still need auth checks
    const TRULY_PUBLIC_PAGES = ['/login', '/signup', '/pricing', '/docs'];
    const isTrulyPublic = TRULY_PUBLIC_PAGES.includes(currentPath);
    
    // Also allow /profile (dashboard) without redirect
    const isProfileDashboard = currentPath === '/profile' || currentPath.startsWith('/profile/');
    
    if (isTrulyPublic || isProfileDashboard) {
        console.log('✅ Allowed page - no redirect needed');
        return;
    }
    
    // Function to perform redirect without history navigation
    function performRedirect(targetUrl, reason) {
        console.log(`🔄 ${reason}`);
        window.location.replace(targetUrl);
        throw new Error('Redirecting...');
    }
    
    // Function to check authentication
    async function checkAuthAndRedirect() {
        try {
            const response = await fetch('/api/method/frappe.auth.get_logged_user', {
                credentials: 'include'
            });
            const data = await response.json();
            const user = data.message;
            
            // Guest user - redirect to login if on protected page
            if (user === 'Guest' || !user) {
                if (isProtectedPage || isAdminPage) {
                    performRedirect('/login', '🔒 Guest user detected on protected page, redirecting to login');
                    return;
                }
                console.log('✅ Guest user on public page - access allowed');
                return;
            }
            
            // Authenticated user
            console.log('✅ Authenticated user:', user);
            
            // Check if user has admin access
            let isAdmin = false;
            try {
                const rolesResponse = await fetch('/api/method/frappe.core.doctype.user.user.has_role', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        role: 'System Manager'
                    }),
                    credentials: 'include'
                });
                const rolesData = await rolesResponse.json();
                isAdmin = rolesData.message === true || rolesData.message === 1;
                
                console.log('   Is Admin:', isAdmin);
                
            } catch (roleError) {
                console.warn('Could not verify admin role:', roleError);
            }
            
            // Admin users can access admin pages
            if (isAdmin && isAdminPage) {
                console.log('✅ Admin user - desk access allowed');
                return;
            }
            
            // Non-admin trying to access admin pages - redirect to dashboard
            if (!isAdmin && isAdminPage) {
                performRedirect('/my-profile', '⚠️ Non-admin trying to access desk, redirecting to dashboard');
                return;
            }
            
            // ENFORCEMENT: Authenticated users on homepage or /me should be on /features
            // BUT: Allow /profile dashboard - users should be able to stay on their dashboard
            if ((currentPath === '/' || currentPath === '/me') && !isProfileDashboard) {
                performRedirect('/features', `🔄 Authenticated user on ${currentPath}, redirecting to features`);
                return;
            }
            
            // Authenticated users can access truly public pages (login, signup, pricing, docs)
            if (isTrulyPublic) {
                console.log('✅ Authenticated user on truly public page - access allowed');
                return;
            }
            
            console.log('✅ Authenticated user - access allowed');
            return;
            
        } catch (error) {
            if (error.message === 'Redirecting...') {
                return;
            }
            console.error('❌ Auth check error:', error);
            // On error, redirect to login only if on protected/admin page
            if (isProtectedPage || isAdminPage) {
                performRedirect('/login', '❌ Auth check failed, redirecting to login');
            }
        }
    }
    
    // Run check immediately
    checkAuthAndRedirect();
    
    console.log('🛡️ Security redirect script loaded');
    
})();
