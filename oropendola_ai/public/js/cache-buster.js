/**
 * Aggressive Cache Buster Utility
 * Prevents browser from caching resources during development
 */

(function() {
    'use strict';
    
    // Generate unique timestamp for each page load
    const CACHE_BUSTER = Date.now() + Math.random().toString(36).substring(7);
    
    // Disable all caching at the document level
    if (document.documentElement) {
        document.documentElement.setAttribute('data-cache-buster', CACHE_BUSTER);
    }
    
    // Override fetch to add cache busting params
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        // Don't modify external URLs
        if (typeof url === 'string' && !url.startsWith('/') && !url.includes(window.location.hostname)) {
            return originalFetch.apply(this, arguments);
        }

        // Don't modify API calls to avoid interfering with POST requests
        if (typeof url === 'string' && url.includes('/api/method/')) {
            return originalFetch.apply(this, arguments);
        }

        // Add cache buster to URL
        const urlObj = new URL(url, window.location.origin);
        urlObj.searchParams.set('_t', Date.now());
        urlObj.searchParams.set('_cb', CACHE_BUSTER);

        // Add aggressive no-cache headers
        const newOptions = options || {};
        newOptions.headers = newOptions.headers || {};
        newOptions.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0';
        newOptions.headers['Pragma'] = 'no-cache';
        newOptions.headers['Expires'] = '0';

        // Force cache mode to no-store
        newOptions.cache = 'no-store';

        return originalFetch.call(this, urlObj.toString(), newOptions);
    };
    
    // Override XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        // Don't modify API calls
        if (typeof url === 'string' && url.includes('/api/method/')) {
            return originalXHROpen.apply(this, [method, url, async, user, password]);
        }

        if (typeof url === 'string' && (url.startsWith('/') || url.includes(window.location.hostname))) {
            const urlObj = new URL(url, window.location.origin);
            urlObj.searchParams.set('_t', Date.now());
            url = urlObj.toString();
        }
        return originalXHROpen.apply(this, [method, url, async, user, password]);
    };
    
    // Prevent back/forward cache
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            console.log('⚠️ Page loaded from cache, forcing reload...');
            window.location.reload(true);
        }
    });
    
    // Add version to all script and link tags
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('script[src], link[href], img[src]').forEach(function(element) {
            const attr = element.tagName === 'SCRIPT' ? 'src' : element.tagName === 'IMG' ? 'src' : 'href';
            const url = element.getAttribute(attr);
            if (url && (url.startsWith('/') || url.startsWith('/assets/')) && !url.includes('?_cb=') && !url.includes('data:')) {
                const separator = url.includes('?') ? '&' : '?';
                element.setAttribute(attr, url + separator + '_cb=' + CACHE_BUSTER + '&_t=' + Date.now());
            }
        });
        
        // Also add to any dynamically loaded content
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'SCRIPT' && node.src) {
                            const url = node.src;
                            if (!url.includes('?_cb=')) {
                                node.src = url + (url.includes('?') ? '&' : '?') + '_cb=' + CACHE_BUSTER;
                            }
                        }
                        if (node.tagName === 'LINK' && node.href) {
                            const url = node.href;
                            if (!url.includes('?_cb=')) {
                                node.href = url + (url.includes('?') ? '&' : '?') + '_cb=' + CACHE_BUSTER;
                            }
                        }
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
    
    // Force reload helper
    window.forceReload = function() {
        // Clear all caches
        if ('caches' in window) {
            caches.keys().then(function(names) {
                names.forEach(function(name) {
                    caches.delete(name);
                });
            });
        }
        
        // Clear localStorage cache items
        try {
            const keysToRemove = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && (key.includes('cache') || key.includes('frappe'))) {
                    keysToRemove.push(key);
                }
            }
            keysToRemove.forEach(key => localStorage.removeItem(key));
        } catch (e) {
            console.warn('Could not clear localStorage:', e);
        }
        
        // Clear sessionStorage
        try {
            sessionStorage.clear();
        } catch (e) {
            console.warn('Could not clear sessionStorage:', e);
        }
        
        // Hard reload
        window.location.reload(true);
    };
    
    // Keyboard shortcut for hard reload (Ctrl+Shift+R)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            console.log('🔄 Force reloading page...');
            window.forceReload();
        }
    });
    
    // Disable service worker if exists
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            registrations.forEach(function(registration) {
                registration.unregister();
            });
        });
    }
    
    console.log('🚀 Aggressive Cache Buster Active');
    console.log('   Timestamp:', CACHE_BUSTER);
    console.log('   Press Ctrl+Shift+R to force reload');
    
    // Periodic check for updates (development only)
    if (window.location.hostname === 'localhost' || window.location.hostname.includes('oropendola')) {
        let lastCheck = Date.now();
        setInterval(function() {
            // Check if page has been inactive
            const now = Date.now();
            const timeDiff = now - lastCheck;
            lastCheck = now;
            
            // If time difference is more than 10 seconds, user might have switched tabs
            // Check for updates when they come back
            if (timeDiff > 10000) {
                fetch(window.location.href, {
                    method: 'HEAD',
                    cache: 'no-store'
                }).then(function(response) {
                    const serverTime = response.headers.get('Last-Modified');
                    if (serverTime) {
                        const stored = sessionStorage.getItem('page-last-modified');
                        if (stored && stored !== serverTime) {
                            console.log('📝 Page updated, reloading...');
                            sessionStorage.setItem('page-last-modified', serverTime);
                            window.location.reload(true);
                        } else if (!stored) {
                            sessionStorage.setItem('page-last-modified', serverTime);
                        }
                    }
                }).catch(function() {
                    // Ignore errors
                });
            }
        }, 5000); // Check every 5 seconds
    }
})();
