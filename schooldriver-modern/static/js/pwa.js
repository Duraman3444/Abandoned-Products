// PWA functionality for SchoolDriver Parent Portal

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.swRegistration = null;
        this.init();
    }

    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('ServiceWorker registration successful');
                
                // Check for updates
                this.swRegistration.addEventListener('updatefound', () => {
                    this.showUpdateAvailable();
                });
            } catch (err) {
                console.log('ServiceWorker registration failed: ', err);
            }
        }

        // Handle install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Check if already installed
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstalledMessage();
        });

        // Request notification permission
        this.requestNotificationPermission();

        // Handle offline/online status
        this.handleConnectionStatus();
    }

    showInstallButton() {
        const installBtn = document.getElementById('install-app-btn');
        if (installBtn) {
            installBtn.style.display = 'block';
            installBtn.addEventListener('click', () => this.installApp());
        } else {
            // Create install button if it doesn't exist
            this.createInstallButton();
        }
    }

    createInstallButton() {
        const button = document.createElement('button');
        button.id = 'install-app-btn';
        button.className = 'btn btn-primary btn-sm install-btn';
        button.innerHTML = '<i class="fas fa-download me-1"></i>Install App';
        button.onclick = () => this.installApp();
        
        // Add to navigation or create floating button
        const nav = document.querySelector('.navbar-nav');
        if (nav) {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.appendChild(button);
            nav.appendChild(li);
        } else {
            // Create floating install button
            button.className += ' floating-install-btn';
            button.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                border-radius: 50px;
                padding: 10px 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(button);
        }
    }

    async installApp() {
        if (!this.deferredPrompt) return;

        this.deferredPrompt.prompt();
        const result = await this.deferredPrompt.userChoice;
        
        if (result.outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
        this.hideInstallButton();
    }

    hideInstallButton() {
        const installBtn = document.getElementById('install-app-btn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    }

    showInstalledMessage() {
        this.showToast('App installed successfully! You can now use SchoolDriver offline.', 'success');
    }

    showUpdateAvailable() {
        this.showToast('A new version is available. Refresh to update.', 'info', 10000);
    }

    async requestNotificationPermission() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notification permission granted');
                this.subscribeToPushNotifications();
            }
        }
    }

    async subscribeToPushNotifications() {
        if (!this.swRegistration) return;

        try {
            // You would need to implement VAPID keys and server-side push notification handling
            // This is a placeholder for the subscription logic
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY_HERE')
            });

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            console.log('Push subscription successful');
        } catch (err) {
            console.log('Push subscription failed: ', err);
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async sendSubscriptionToServer(subscription) {
        // Send subscription to Django backend
        try {
            await fetch('/api/push-subscription/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription
                })
            });
        } catch (err) {
            console.log('Failed to send subscription to server: ', err);
        }
    }

    handleConnectionStatus() {
        const updateOnlineStatus = () => {
            const statusIndicator = document.getElementById('connection-status');
            if (navigator.onLine) {
                if (statusIndicator) statusIndicator.style.display = 'none';
                this.syncOfflineData();
            } else {
                this.showOfflineIndicator();
            }
        };

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        updateOnlineStatus(); // Check initial status
    }

    showOfflineIndicator() {
        let indicator = document.getElementById('connection-status');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'connection-status';
            indicator.className = 'alert alert-warning offline-indicator';
            indicator.innerHTML = `
                <i class="fas fa-wifi me-2"></i>
                You're offline. Some features may be limited.
            `;
            indicator.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1050;
                margin: 0;
                border-radius: 0;
                text-align: center;
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    async syncOfflineData() {
        // Sync any offline actions when coming back online
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                await this.swRegistration.sync.register('background-sync');
            } catch (err) {
                console.log('Background sync registration failed: ', err);
            }
        }
    }

    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} toast-notification`;
        toast.innerHTML = `
            <span>${message}</span>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1060;
            max-width: 300px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }

    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Grade check widget functionality
class GradeWidget {
    constructor() {
        this.initWidget();
    }

    async initWidget() {
        if (!this.shouldShowWidget()) return;

        await this.createWidget();
        this.updateWidget();
        
        // Update every 30 minutes
        setInterval(() => this.updateWidget(), 30 * 60 * 1000);
    }

    shouldShowWidget() {
        // Only show on dashboard and main pages
        const path = window.location.pathname;
        return path.includes('/parent/') || path === '/';
    }

    async createWidget() {
        const widget = document.createElement('div');
        widget.id = 'grade-widget';
        widget.className = 'grade-widget card';
        widget.innerHTML = `
            <div class="card-body">
                <h6 class="card-title">
                    <i class="fas fa-chart-line me-2"></i>Quick Grade Check
                </h6>
                <div id="widget-content">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        `;
        
        widget.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 280px;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            max-height: 400px;
            overflow-y: auto;
        `;
        
        document.body.appendChild(widget);
    }

    async updateWidget() {
        const widget = document.getElementById('grade-widget');
        if (!widget) return;

        try {
            const response = await fetch('/parent/api/quick-grades/');
            const data = await response.json();
            
            const content = document.getElementById('widget-content');
            content.innerHTML = this.renderGradeData(data);
        } catch (err) {
            console.log('Failed to update grade widget: ', err);
            // Use cached data if available
            this.showCachedData();
        }
    }

    renderGradeData(data) {
        if (!data.children || data.children.length === 0) {
            return '<p class="text-muted">No grade data available</p>';
        }

        let html = '';
        data.children.forEach(child => {
            html += `
                <div class="mb-2">
                    <strong>${child.name}</strong>
                    <div class="text-muted small">GPA: ${child.gpa || 'N/A'}</div>
                    ${child.recent_grades.map(grade => 
                        `<div class="small">${grade.subject}: ${grade.grade}</div>`
                    ).join('')}
                </div>
            `;
        });
        
        return html;
    }

    showCachedData() {
        // Implementation to show cached grade data
        const content = document.getElementById('widget-content');
        content.innerHTML = '<p class="text-muted small">Showing cached data (offline)</p>';
    }
}

// Initialize PWA when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const pwa = new PWAManager();
    const gradeWidget = new GradeWidget();
});
