/**
 * Live Analytics Module
 * Continuously updating Chart.js line graph for real-time dashboard metrics
 */

class LiveAnalytics {
    constructor(canvasId, options = {}) {
        this.canvasId = canvasId;
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas?.getContext('2d');
        
        if (!this.canvas || !this.ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return;
        }

        // Configuration
        this.maxDataPoints = options.maxDataPoints || 50;
        this.updateInterval = options.updateInterval || 2000; // 2 seconds
        this.maxFPS = options.maxFPS || 30;
        this.paused = false;
        
        // Data storage
        this.dataPoints = [];
        this.labels = [];
        this.startTime = Date.now();
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / this.maxFPS;
        
        // Animation handles
        this.updateTimer = null;
        this.animationFrame = null;
        
        // Chart instance
        this.chart = null;
        
        // Bind methods
        this.update = this.update.bind(this);
        this.animate = this.animate.bind(this);
        this.pause = this.pause.bind(this);
        this.resume = this.resume.bind(this);
        
        this.initializeChart();
        this.start();
    }

    /**
     * Initialize Chart.js line chart
     */
    initializeChart() {
        const chartConfig = {
            type: 'line',
            data: {
                labels: this.labels,
                datasets: [{
                    label: 'Live Metrics',
                    data: this.dataPoints,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Live Analytics Stream',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        color: '#333'
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const timestamp = context[0].label;
                                return `Time: ${timestamp}`;
                            },
                            label: function(context) {
                                return `Value: ${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time',
                            font: {
                                size: 12
                            }
                        },
                        ticks: {
                            maxTicksLimit: 6,
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Value',
                            font: {
                                size: 12
                            }
                        },
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                animation: {
                    duration: 500,
                    easing: 'easeInOutQuart'
                },
                elements: {
                    line: {
                        tension: 0.4
                    }
                }
            }
        };

        this.chart = new Chart(this.ctx, chartConfig);
    }

    /**
     * Generate realistic random data point
     */
    generateDataPoint() {
        const now = Date.now();
        const elapsed = (now - this.startTime) / 1000; // seconds elapsed
        
        // Simulate realistic data with trends and noise
        const baseValue = 50 + Math.sin(elapsed / 10) * 20; // Slow sine wave
        const noise = (Math.random() - 0.5) * 10; // Random noise
        const trend = elapsed * 0.1; // Slight upward trend
        
        return Math.max(0, Math.min(100, baseValue + noise + trend % 40));
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * Add new data point to the chart
     */
    addDataPoint() {
        const timestamp = Date.now();
        const value = this.generateDataPoint();
        const timeLabel = this.formatTimestamp(timestamp);
        
        // Add new data point
        this.dataPoints.push(value);
        this.labels.push(timeLabel);
        
        // Remove oldest point if we exceed max points (sliding window)
        if (this.dataPoints.length > this.maxDataPoints) {
            this.dataPoints.shift();
            this.labels.shift();
        }
        
        // Fire custom event for testing
        this.canvas.dispatchEvent(new CustomEvent('dataPointAdded', {
            detail: { value, timestamp, totalPoints: this.dataPoints.length }
        }));
    }

    /**
     * Update chart with animation frame limiting
     */
    animate(currentTime) {
        if (!this.paused) {
            // Limit frame rate
            if (currentTime - this.lastFrameTime >= this.frameInterval) {
                this.chart.update('none'); // Update without animation for smoother performance
                this.lastFrameTime = currentTime;
            }
            
            this.animationFrame = requestAnimationFrame(this.animate);
        }
    }

    /**
     * Main update function called by setInterval
     */
    update() {
        if (!this.paused) {
            this.addDataPoint();
        }
    }

    /**
     * Start the live analytics stream
     */
    start() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        // Start data updates
        this.updateTimer = setInterval(this.update, this.updateInterval);
        
        // Start animation loop
        this.paused = false;
        this.animationFrame = requestAnimationFrame(this.animate);
        
        console.log('Live Analytics started');
    }

    /**
     * Pause the analytics stream
     */
    pause() {
        this.paused = true;
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        console.log('Live Analytics paused');
    }

    /**
     * Resume the analytics stream
     */
    resume() {
        if (this.paused) {
            this.paused = false;
            this.animationFrame = requestAnimationFrame(this.animate);
            console.log('Live Analytics resumed');
        }
    }

    /**
     * Toggle pause/resume state
     */
    toggle() {
        if (this.paused) {
            this.resume();
        } else {
            this.pause();
        }
        return !this.paused; // Return new state (true = running)
    }

    /**
     * Stop and destroy the analytics stream
     */
    destroy() {
        this.pause();
        
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        console.log('Live Analytics destroyed');
    }

    /**
     * Get current status
     */
    getStatus() {
        return {
            paused: this.paused,
            dataPoints: this.dataPoints.length,
            maxDataPoints: this.maxDataPoints,
            updateInterval: this.updateInterval,
            uptime: Date.now() - this.startTime
        };
    }

    /**
     * Get current data for testing
     */
    getData() {
        return {
            labels: [...this.labels],
            data: [...this.dataPoints]
        };
    }
}

// Global instance for dashboard
let dashboardLiveAnalytics = null;

/**
 * Initialize live analytics on dashboard
 */
function initializeLiveAnalytics(canvasId = 'liveAnalyticsChart', options = {}) {
    // Destroy existing instance
    if (dashboardLiveAnalytics) {
        dashboardLiveAnalytics.destroy();
    }
    
    // Create new instance
    dashboardLiveAnalytics = new LiveAnalytics(canvasId, options);
    
    // Setup pause/resume button if it exists
    const pauseButton = document.getElementById('pauseLiveAnalytics');
    if (pauseButton) {
        pauseButton.addEventListener('click', function() {
            const isRunning = dashboardLiveAnalytics.toggle();
            this.textContent = isRunning ? 'Pause' : 'Resume';
            this.className = isRunning ? 'btn btn-outline-warning btn-sm' : 'btn btn-outline-success btn-sm';
        });
    }
    
    return dashboardLiveAnalytics;
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    if (dashboardLiveAnalytics) {
        dashboardLiveAnalytics.destroy();
    }
});

// Export for testing and external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LiveAnalytics, initializeLiveAnalytics };
} else {
    window.LiveAnalytics = LiveAnalytics;
    window.initializeLiveAnalytics = initializeLiveAnalytics;
}
