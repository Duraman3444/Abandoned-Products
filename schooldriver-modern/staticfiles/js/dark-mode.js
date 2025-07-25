/**
 * Dark Mode Toggle System
 * Manages theme switching and persistence across the application
 */

class DarkModeManager {
    constructor() {
        this.init();
    }

    init() {
        // Load saved theme preference or default to light
        this.currentTheme = this.getSavedTheme() || 'light';
        this.applyTheme(this.currentTheme);
        this.setupToggleButton();
        this.setupSystemThemeDetection();
    }

    getSavedTheme() {
        return localStorage.getItem('schooldriver-theme');
    }

    saveTheme(theme) {
        localStorage.setItem('schooldriver-theme', theme);
    }

    applyTheme(theme) {
        const root = document.documentElement;
        const body = document.body;
        
        // Remove existing theme classes
        body.classList.remove('theme-light', 'theme-dark');
        root.setAttribute('data-theme', theme);
        body.classList.add(`theme-${theme}`);
        
        // Update theme-aware elements
        this.updateThemeAwareElements(theme);
        
        // Update toggle button
        this.updateToggleButton(theme);
        
        // Emit theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    updateThemeAwareElements(theme) {
        // Update Bootstrap classes for cards, tables, etc.
        const cards = document.querySelectorAll('.card');
        const tables = document.querySelectorAll('.table');
        const modals = document.querySelectorAll('.modal-content');
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        
        cards.forEach(card => {
            if (theme === 'dark') {
                card.classList.add('bg-dark', 'text-light');
                card.classList.remove('bg-light');
            } else {
                card.classList.remove('bg-dark', 'text-light');
                card.classList.add('bg-light');
            }
        });
        
        tables.forEach(table => {
            if (theme === 'dark') {
                table.classList.add('table-dark');
            } else {
                table.classList.remove('table-dark');
            }
        });
        
        modals.forEach(modal => {
            if (theme === 'dark') {
                modal.classList.add('bg-dark', 'text-light');
            } else {
                modal.classList.remove('bg-dark', 'text-light');
            }
        });
        
        dropdowns.forEach(dropdown => {
            if (theme === 'dark') {
                dropdown.classList.add('dropdown-menu-dark');
            } else {
                dropdown.classList.remove('dropdown-menu-dark');
            }
        });
    }

    updateToggleButton(theme) {
        const toggleBtn = document.getElementById('darkModeToggle');
        const toggleIcon = document.querySelector('#darkModeToggle i');
        
        if (toggleBtn && toggleIcon) {
            if (theme === 'dark') {
                toggleIcon.className = 'fas fa-sun';
                toggleBtn.title = 'Switch to Light Mode';
                toggleBtn.setAttribute('aria-label', 'Switch to Light Mode');
            } else {
                toggleIcon.className = 'fas fa-moon';
                toggleBtn.title = 'Switch to Dark Mode';
                toggleBtn.setAttribute('aria-label', 'Switch to Dark Mode');
            }
        }
    }

    setupToggleButton() {
        const toggleBtn = document.getElementById('darkModeToggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    setupSystemThemeDetection() {
        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (!this.getSavedTheme()) {
                    // Only auto-switch if user hasn't manually set a preference
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.currentTheme = newTheme;
        this.saveTheme(newTheme);
        this.applyTheme(newTheme);
        
        // Show feedback
        this.showThemeChangeToast(newTheme);
    }

    showThemeChangeToast(theme) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white ${theme === 'dark' ? 'bg-dark' : 'bg-primary'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${theme === 'dark' ? 'moon' : 'sun'} me-2"></i>
                    Switched to ${theme === 'dark' ? 'Dark' : 'Light'} Mode
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Public methods for manual theme control
    setTheme(theme) {
        if (['light', 'dark'].includes(theme)) {
            this.currentTheme = theme;
            this.saveTheme(theme);
            this.applyTheme(theme);
        }
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    // Initialize theme-aware components
    initializeThemeAwareComponents() {
        // Initialize charts with theme-appropriate colors
        if (window.Chart) {
            Chart.defaults.color = this.currentTheme === 'dark' ? '#E6EDF3' : '#666';
            Chart.defaults.borderColor = this.currentTheme === 'dark' ? '#30363D' : '#E9ECEF';
            Chart.defaults.backgroundColor = this.currentTheme === 'dark' ? '#21262D' : '#F8F9FA';
        }
        
        // Update any existing charts
        if (window.chartInstances) {
            Object.values(window.chartInstances).forEach(chart => {
                chart.update();
            });
        }
    }
}

// Keyboard shortcut for theme toggle
document.addEventListener('keydown', function(e) {
    // Ctrl+Shift+D (or Cmd+Shift+D on Mac) to toggle theme
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        if (window.darkModeManager) {
            window.darkModeManager.toggleTheme();
        }
    }
});

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.darkModeManager = new DarkModeManager();
});

// Listen for theme changes to update components
window.addEventListener('themeChanged', function(e) {
    if (window.darkModeManager) {
        window.darkModeManager.initializeThemeAwareComponents();
    }
});

// Export for use in other scripts
window.DarkModeManager = DarkModeManager;
