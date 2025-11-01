/**
 * Dynamic Navigation Component
 * Handles authentication-based navigation for all pages
 */

(function() {
    'use strict';

    const API_BASE = window.location.origin;
    let currentUser = null;
    let isAuthenticated = false;

    /**
     * Check user authentication status
     */
    async function checkAuth() {
        try {
            // Always check with server - sid cookie is httpOnly so we can't read it
            // This is the ONLY reliable way to determine auth state
            const response = await fetch(`${API_BASE}/api/method/frappe.auth.get_logged_user`, {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // If response not OK, check if it's a 403 (unauthorized) or other error
            if (!response.ok) {
                if (response.status === 403 || response.status === 401) {
                    // Definitely not logged in
                    console.log('❌ Auth check: User not authenticated (403/401)');
                    currentUser = null;
                    isAuthenticated = false;
                    return false;
                } else {
                    // Server error - keep current state
                    console.warn('⚠️ Auth check: Server error, keeping current state');
                    return isAuthenticated;
                }
            }

            const data = await response.json();
            console.log('📡 Auth check response:', data);

            if (data.message && data.message !== 'Guest') {
                currentUser = data.message;
                isAuthenticated = true;
                console.log('✅ User authenticated:', currentUser);
            } else {
                // API explicitly says user is Guest - they're logged out
                currentUser = null;
                isAuthenticated = false;
                console.log('👤 User is Guest (not authenticated)');
            }

            return isAuthenticated;
        } catch (error) {
            // Network error or other exception - KEEP current state
            // Don't log out user just because API call failed
            console.warn('⚠️ Auth check failed, keeping current state:', error);
            return isAuthenticated;
        }
    }

    /**
     * Update navigation based on auth status
     */
    function updateNavigation() {
        const currentPath = window.location.pathname;
        const navLinksContainer = document.querySelector('.nav-links');
        const mobileMenuItems = document.querySelector('.mobile-menu-items');
        const logoLink = document.querySelector('.logo');
        
        if (!navLinksContainer) return;

        // Update logo link based on auth status
        if (logoLink) {
            if (isAuthenticated) {
                // Authenticated users: logo goes to /features
                logoLink.href = '/features';
            } else {
                // Non-authenticated users: logo goes to home
                logoLink.href = '/';
            }
        }

        // Desktop navigation
        if (isAuthenticated) {
            // Authenticated user navigation
            navLinksContainer.innerHTML = `
                <a href="/features" ${currentPath === '/features' ? 'class="active"' : ''}>Features</a>
                <a href="/pricing" ${currentPath === '/pricing' ? 'class="active"' : ''}>Pricing</a>
                <a href="/docs" ${currentPath === '/docs' ? 'class="active"' : ''}>Docs</a>
                <a href="/my-profile" ${currentPath === '/my-profile' ? 'class="active"' : ''}>My Profile</a>
                <button class="btn-logout" onclick="window.DynamicNav.logout()">Logout</button>
            `;
        } else {
            // Non-authenticated user navigation
            // Use /#features anchor ONLY on homepage, /features on other pages
            const featuresHref = currentPath === '/' ? '/#features' : '/features';
            navLinksContainer.innerHTML = `
                <a href="${featuresHref}" ${currentPath === '/' || currentPath.includes('#features') ? 'class="active"' : ''}>Features</a>
                <a href="/pricing" ${currentPath === '/pricing' ? 'class="active"' : ''}>Pricing</a>
                <a href="/docs" ${currentPath === '/docs' ? 'class="active"' : ''}>Docs</a>
                <a href="/login" class="btn-secondary">Sign In</a>
                <a href="/login#signup" class="btn-primary">Get Started</a>
            `;
        }

        // Mobile navigation
        if (mobileMenuItems) {
            if (isAuthenticated) {
                // Authenticated user mobile menu
                mobileMenuItems.innerHTML = `
                    <a href="/features" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Features <span>→</span>
                    </a>
                    <a href="/pricing" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Pricing <span>→</span>
                    </a>
                    <a href="/docs" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Docs <span>→</span>
                    </a>
                    <a href="/my-profile" class="mobile-menu-item primary" onclick="closeMobileMenu()">
                        My Profile
                    </a>
                    <button class="mobile-menu-item" onclick="window.DynamicNav.logout()" style="background: transparent; color: #FF5F56; border: 1px solid #FF5F56; justify-content: center;">
                        Logout
                    </button>
                `;
            } else {
                // Non-authenticated user mobile menu
                // Use /#features anchor ONLY on homepage, /features on other pages
                const featuresHref = currentPath === '/' ? '/#features' : '/features';
                mobileMenuItems.innerHTML = `
                    <a href="${featuresHref}" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Features <span>→</span>
                    </a>
                    <a href="/pricing" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Pricing <span>→</span>
                    </a>
                    <a href="/docs" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Docs <span>→</span>
                    </a>
                    <a href="/login" class="mobile-menu-item" onclick="closeMobileMenu()">
                        Sign In <span>→</span>
                    </a>
                    <a href="/login#signup" class="mobile-menu-item primary" onclick="closeMobileMenu()">
                        Get Started
                    </a>
                `;
            }
        }

        // Add logout button styles if not present
        addLogoutStyles();

        // Remove flash prevention styles now that navigation is updated
        const navFlashFix = document.getElementById('nav-flash-fix');
        if (navFlashFix) {
            navFlashFix.remove();
        }

        // Make navigation visible (CSS hides it by default)
        const navLinks = document.querySelector('.nav-links');
        if (navLinks) {
            navLinks.style.visibility = 'visible';
        }
    }

    /**
     * Add logout button styles
     */
    function addLogoutStyles() {
        if (document.getElementById('dynamic-nav-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'dynamic-nav-styles';
        style.textContent = `
            .btn-logout {
                padding: 10px 20px;
                background: transparent;
                color: #FF5F56;
                border: 1px solid #FF5F56;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s;
                cursor: pointer;
                font-size: 14px;
                font-family: 'Inter', sans-serif;
            }

            .btn-logout:hover {
                background: #FF5F56;
                color: white;
                transform: translateY(-2px);
            }

            .nav-links a.active {
                color: var(--text-primary, #FFFFFF);
                position: relative;
            }

            .nav-links a.active::after {
                content: '';
                position: absolute;
                bottom: -8px;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(135deg, #7B61FF 0%, #00D9FF 100%);
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Handle user logout
     */
    async function logout() {
        try {
            await fetch(`${API_BASE}/api/method/logout`, {
                method: 'POST',
                credentials: 'include'
            });
            window.location.href = '/';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/';
        }
    }

    /**
     * Initialize dynamic navigation
     */
    async function init() {
        // CRITICAL FIX: Frappe's sid cookie is httpOnly and can't be read by JavaScript
        // We MUST rely on the API call to determine auth state
        // Start by assuming logged out to prevent flash
        isAuthenticated = false;

        // Try to check for alternative cookies that might indicate login
        // Frappe sets 'user_id' and 'full_name' cookies that are readable
        const hasUserCookie = document.cookie.includes('user_id=') ||
                              document.cookie.includes('full_name=') ||
                              document.cookie.includes('system_user=');

        if (hasUserCookie) {
            // User cookies present - likely logged in
            isAuthenticated = true;
            console.log('🔐 User cookies detected, assuming logged in');
        } else {
            console.log('🔓 No user cookies detected, assuming logged out');
        }

        // Store initial state for comparison
        const initialAuthState = isAuthenticated;

        // Update navigation immediately with assumed state (no flash!)
        updateNavigation();

        // VERIFICATION PATH: Verify auth state with server (async)
        // This is the ONLY reliable way to check auth (sid cookie is httpOnly)
        await checkAuth();

        // Update again ONLY if verification changed the auth state
        // This prevents overwriting correct nav with wrong state
        if (isAuthenticated !== initialAuthState) {
            console.log('🔄 Auth state changed from', initialAuthState, 'to', isAuthenticated);
            updateNavigation();
        } else {
            console.log('✅ Auth state confirmed:', isAuthenticated);
        }
    }

    // Public API
    window.DynamicNav = {
        init: init,
        logout: logout,
        isAuthenticated: () => isAuthenticated,
        getCurrentUser: () => currentUser
    };

    // Auto-initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
