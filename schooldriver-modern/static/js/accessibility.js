/**
 * Accessibility improvements for SchoolDriver Modern
 * Includes keyboard navigation, focus management, and ARIA live regions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add skip to main content link
    addSkipLink();
    
    // Enhance keyboard navigation
    enhanceKeyboardNavigation();
    
    // Improve focus management
    improveFocusManagement();
    
    // Add ARIA live regions for dynamic content
    addLiveRegions();
    
    // Enhance form accessibility
    enhanceFormAccessibility();
});

/**
 * Add skip to main content link for screen readers and keyboard users
 */
function addSkipLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'sr-only sr-only-focusable btn btn-primary position-absolute';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        z-index: 9999;
        padding: 8px 16px;
        transition: top 0.3s;
    `;
    
    // Only show when focused
    skipLink.addEventListener('focus', function() {
        this.style.top = '10px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    // Insert as first element in body
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content landmark if it doesn't exist
    const mainContent = document.querySelector('[role="main"], main');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    } else if (!mainContent) {
        const content = document.querySelector('.container-fluid, .container');
        if (content) {
            content.setAttribute('role', 'main');
            content.id = 'main-content';
        }
    }
}

/**
 * Enhance keyboard navigation throughout the application
 */
function enhanceKeyboardNavigation() {
    // Add keyboard support for cards and clickable elements
    const clickableCards = document.querySelectorAll('.card[data-href], .clickable');
    clickableCards.forEach(card => {
        if (!card.hasAttribute('tabindex')) {
            card.setAttribute('tabindex', '0');
        }
        
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const href = card.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                } else {
                    card.click();
                }
            }
        });
    });
    
    // Add arrow key navigation for tab-like interfaces
    const tabLists = document.querySelectorAll('[role="tablist"]');
    tabLists.forEach(tabList => {
        const tabs = tabList.querySelectorAll('[role="tab"]');
        tabs.forEach((tab, index) => {
            tab.addEventListener('keydown', function(e) {
                let newIndex = index;
                
                switch(e.key) {
                    case 'ArrowRight':
                    case 'ArrowDown':
                        e.preventDefault();
                        newIndex = (index + 1) % tabs.length;
                        break;
                    case 'ArrowLeft':
                    case 'ArrowUp':
                        e.preventDefault();
                        newIndex = (index - 1 + tabs.length) % tabs.length;
                        break;
                    case 'Home':
                        e.preventDefault();
                        newIndex = 0;
                        break;
                    case 'End':
                        e.preventDefault();
                        newIndex = tabs.length - 1;
                        break;
                    default:
                        return;
                }
                
                tabs[newIndex].focus();
                tabs[newIndex].click();
            });
        });
    });
    
    // Improve dropdown and modal keyboard navigation
    enhanceDropdownKeyboard();
}

/**
 * Enhance dropdown keyboard navigation
 */
function enhanceDropdownKeyboard() {
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        const items = menu ? menu.querySelectorAll('.dropdown-item') : [];
        
        if (toggle && menu) {
            toggle.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    menu.classList.add('show');
                    items[0]?.focus();
                }
            });
            
            items.forEach((item, index) => {
                item.addEventListener('keydown', function(e) {
                    switch(e.key) {
                        case 'ArrowDown':
                            e.preventDefault();
                            items[(index + 1) % items.length]?.focus();
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            items[(index - 1 + items.length) % items.length]?.focus();
                            break;
                        case 'Escape':
                            e.preventDefault();
                            menu.classList.remove('show');
                            toggle.focus();
                            break;
                        case 'Home':
                            e.preventDefault();
                            items[0]?.focus();
                            break;
                        case 'End':
                            e.preventDefault();
                            items[items.length - 1]?.focus();
                            break;
                    }
                });
            });
        }
    });
}

/**
 * Improve focus management for dynamic content
 */
function improveFocusManagement() {
    // Store focus before page transitions
    let lastFocusedElement = null;
    
    document.addEventListener('beforeunload', function() {
        lastFocusedElement = document.activeElement;
    });
    
    // Focus management for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const focusableElement = modal.querySelector('[autofocus], .btn-primary, .form-control');
            if (focusableElement) {
                focusableElement.focus();
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            const trigger = document.querySelector(`[data-bs-target="#${modal.id}"]`);
            if (trigger) {
                trigger.focus();
            }
        });
    });
    
    // Focus management for alerts that appear dynamically
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList && node.classList.contains('alert')) {
                        // Announce the alert to screen readers
                        announceToScreenReader(node.textContent);
                    }
                });
            });
        });
        
        observer.observe(alertContainer, { childList: true });
    }
}

/**
 * Add ARIA live regions for dynamic content announcements
 */
function addLiveRegions() {
    // Create polite live region for status updates
    const politeRegion = document.createElement('div');
    politeRegion.setAttribute('aria-live', 'polite');
    politeRegion.setAttribute('aria-atomic', 'true');
    politeRegion.className = 'sr-only';
    politeRegion.id = 'live-region-polite';
    document.body.appendChild(politeRegion);
    
    // Create assertive live region for urgent announcements
    const assertiveRegion = document.createElement('div');
    assertiveRegion.setAttribute('aria-live', 'assertive');
    assertiveRegion.setAttribute('aria-atomic', 'true');
    assertiveRegion.className = 'sr-only';
    assertiveRegion.id = 'live-region-assertive';
    document.body.appendChild(assertiveRegion);
}

/**
 * Enhance form accessibility
 */
function enhanceFormAccessibility() {
    // Add required indicators
    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
    requiredFields.forEach(field => {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label && !label.querySelector('.required-indicator')) {
            const indicator = document.createElement('span');
            indicator.className = 'required-indicator text-danger';
            indicator.setAttribute('aria-label', 'required');
            indicator.textContent = ' *';
            label.appendChild(indicator);
        }
        
        // Add aria-required if not present
        if (!field.hasAttribute('aria-required')) {
            field.setAttribute('aria-required', 'true');
        }
    });
    
    // Enhance error messaging
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        const errorMessage = field.parentElement.querySelector('.invalid-feedback');
        if (errorMessage && !errorMessage.id) {
            errorMessage.id = `${field.id}-error`;
            field.setAttribute('aria-describedby', errorMessage.id);
        }
    });
    
    // Add form validation announcements
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const errors = form.querySelectorAll('.is-invalid');
            if (errors.length > 0) {
                announceToScreenReader(`Form has ${errors.length} error${errors.length === 1 ? '' : 's'}. Please review and correct.`);
                errors[0].focus();
            }
        });
    });
}

/**
 * Announce message to screen readers using live regions
 */
function announceToScreenReader(message, urgent = false) {
    const regionId = urgent ? 'live-region-assertive' : 'live-region-polite';
    const region = document.getElementById(regionId);
    
    if (region) {
        region.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            region.textContent = '';
        }, 1000);
    }
}

/**
 * Add high contrast mode detection and support
 */
function addHighContrastSupport() {
    // Detect if user prefers high contrast
    if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
        document.body.classList.add('high-contrast');
    }
    
    // Listen for changes in contrast preference
    if (window.matchMedia) {
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');
        contrastQuery.addEventListener('change', function(e) {
            if (e.matches) {
                document.body.classList.add('high-contrast');
            } else {
                document.body.classList.remove('high-contrast');
            }
        });
    }
}

/**
 * Add reduced motion support
 */
function addReducedMotionSupport() {
    // Detect if user prefers reduced motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.body.classList.add('reduce-motion');
        
        // Disable CSS animations and transitions
        const style = document.createElement('style');
        style.textContent = `
            .reduce-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize additional accessibility features
addHighContrastSupport();
addReducedMotionSupport();

// Export functions for use in other scripts
window.accessibility = {
    announceToScreenReader,
    addSkipLink,
    enhanceKeyboardNavigation,
    improveFocusManagement
};
