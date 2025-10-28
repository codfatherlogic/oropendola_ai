/**
 * Global Security Redirect Script
 * Ensures authenticated users are always on /my-profile
 * Redirects guest users to /login
 * Optimized to prevent browser history navigation flicker
 */

(function() {
    'use strict';
    
    // List of allowed public pages (no redirect needed for guests)
    const PUBLIC_PAGES = [
        '/login',
        '/signup',
        '/pricing',
        '/docs'
    ];
    
    // List of admin-only pages
    const ADMIN_PAGES = [
        '/app',
        '/desk'
    ];
    
    // Get current path
    const currentPath = window.location.pathname;
    
    // Check if current page is public or dashboard
    const isPublicPage = PUBLIC_PAGES.some(page => currentPath === page || currentPath.startsWith(page));
    const isAdminPage = ADMIN_PAGES.some(page => currentPath.startsWith(page));
    const isDashboard = currentPath === '/my-profile' || currentPath.startsWith('/my-profile');
    const isHomepage = currentPath === '/' || currentPath === '/index' || currentPath === '/index.html';
    
    // Early exit if already on dashboard - no need to check auth
    if (isDashboard) {
        console.log('🛡️ Already on dashboard, skipping redirect check');
        return;
    }
    
    // Function to perform redirect without history navigation
    function performRedirect(targetUrl, reason) {
        console.log(`🔄 ${reason}`);
        
        // Use replace to avoid adding to browser history
        // This prevents the back/forward navigation effect
        window.location.replace(targetUrl);
        
        // Stop all script execution to prevent any flash of content
        throw new Error('Redirecting...');
    }
    
    // Function to check authentication and redirect
    async function checkAuthAndRedirect() {
        try {
            const response = await fetch('/api/method/frappe.auth.get_logged_user', {
                credentials: 'include'
            });
            const data = await response.json();
            const user = data.message;
            
            // Guest user
            if (user === 'Guest' || !user) {
                // Homepage is allowed for guests
                if (isHomepage) {
                    return;
                }
                // If not on a public page, redirect to login
                if (!isPublicPage && !isDashboard) {
                    performRedirect('/login', '🔒 Guest user detected, redirecting to login');
                    return;
                }
                // If on dashboard, also redirect to login
                if (isDashboard) {
                    performRedirect('/login', '🔒 Guest trying to access dashboard, redirecting to login');
                    return;
                }
                return;
            }
            
            // Authenticated user
            console.log('✅ Authenticated user:', user);
            
            // Check if user has admin access
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
            const isAdmin = rolesData.message === true || rolesData.message === 1;
            
            // Admin users can access admin pages
            if (isAdmin && isAdminPage) {
                console.log('👤 Admin user accessing desk');
                return;
            }
            
            // Non-admin trying to access admin pages - redirect to dashboard
            if (!isAdmin && isAdminPage) {
                performRedirect('/my-profile', '⚠️ Non-admin trying to access desk, redirecting to dashboard');
                return;
            }
            
            // Authenticated non-admin on homepage - redirect to dashboard immediately
            if (!isAdmin && isHomepage) {
                performRedirect('/my-profile', '🔄 Redirecting authenticated user from homepage to dashboard');
                return;
            }
            
            // Authenticated non-admin on any page except dashboard or public pages
            // Redirect to dashboard
            if (!isAdmin && !isDashboard && !isPublicPage) {
                performRedirect('/my-profile', `🔄 Redirecting authenticated user to dashboard from: ${currentPath}`);
                return;
            }
            
        } catch (error) {
            // Check if it's our intentional redirect error
            if (error.message === 'Redirecting...') {
                // This is expected - we're redirecting
                return;
            }
            
            console.error('❌ Auth check error:', error);
            // On error, redirect to login for safety (except homepage)
            if (!isPublicPage && !isHomepage) {
                performRedirect('/login', '❌ Auth check failed, redirecting to login');
            }
        }
    }
    
    // Run check immediately (no DOM wait for critical redirects)
    checkAuthAndRedirect();
    
    console.log('🛡️ Security redirect script loaded');
    console.log('   Current path:', currentPath);
    console.log('   Is public page:', isPublicPage);
    console.log('   Is homepage:', isHomepage);
    console.log('   Is dashboard:', isDashboard);
    console.log('   Is admin page:', isAdminPage);
})();
