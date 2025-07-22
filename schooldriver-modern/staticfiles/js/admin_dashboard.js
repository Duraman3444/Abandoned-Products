// Admin Dashboard Chart Initialization
// Fixes for canvas height and CSP compliance

// Dashboard data (will be set by template)
let dashboardData = null;

// Chart instances
let pipelineChart, documentsChart, statusChart, trendsChart;

// Theme management
function setTheme(theme) {
    const adminDashboard = document.getElementById('adminDashboard');
    const themeToggle = document.getElementById('themeToggle');
    
    if (theme === 'light') {
        adminDashboard.classList.add('light-mode');
        themeToggle.textContent = '🌙 Dark Mode';
    } else {
        adminDashboard.classList.remove('light-mode');
        themeToggle.textContent = '☀️ Light Mode';
    }
    
    // Update chart colors based on theme
    if (window.Chart && dashboardData) {
        updateChartTheme(theme);
    }
}

function updateChartTheme(theme) {
    const textColor = theme === 'light' ? '#333333' : '#e0e0e0';
    const gridColor = theme === 'light' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)';
    
    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;
    
    // Reinitialize charts with new theme
    if (pipelineChart) initializeCharts();
}

// Chart initialization with improved timing and canvas height handling
function initializeCharts() {
    if (!dashboardData) {
        console.warn('Dashboard data not available');
        return;
    }
    
    const theme = document.getElementById('adminDashboard').classList.contains('light-mode') ? 'light' : 'dark';
    const textColor = theme === 'light' ? '#333333' : '#e0e0e0';
    const gridColor = theme === 'light' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)';
    
    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;
    
    // Destroy existing charts
    if (pipelineChart) pipelineChart.destroy();
    if (documentsChart) documentsChart.destroy();
    if (statusChart) statusChart.destroy();
    if (trendsChart) trendsChart.destroy();
    
    // 1. Pipeline Chart (Horizontal Bar)
    const pipelineCtx = document.getElementById('pipelineChart');
    if (pipelineCtx) {
        try {
            pipelineChart = new Chart(pipelineCtx, {
                type: 'bar',
                data: {
                    labels: dashboardData.pipeline.labels,
                    datasets: [{
                        label: 'Applicants',
                        data: dashboardData.pipeline.values,
                        backgroundColor: dashboardData.pipeline.colors,
                        borderColor: dashboardData.pipeline.colors.map(color => color + 'CC'),
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { 
                            beginAtZero: true,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        y: {
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating pipeline chart:', error);
            showNoDataMessage('pipelineChart');
        }
    }
    
    // 2. Documents Chart (Vertical Bar)
    const documentsCtx = document.getElementById('documentsChart');
    if (documentsCtx) {
        try {
            documentsChart = new Chart(documentsCtx, {
                type: 'bar',
                data: {
                    labels: dashboardData.documents.labels,
                    datasets: [{
                        label: 'Completion Rate (%)',
                        data: dashboardData.documents.completion_rates,
                        backgroundColor: dashboardData.documents.colors,
                        borderColor: dashboardData.documents.colors.map(color => color + 'CC'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        y: { 
                            beginAtZero: true,
                            max: 100,
                            ticks: { 
                                color: textColor,
                                callback: value => value + '%' 
                            },
                            grid: { color: gridColor }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating documents chart:', error);
            showNoDataMessage('documentsChart');
        }
    }
    
    // 3. Status Chart (Pie Chart) - Critical Fix
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        try {
            // Ensure canvas has proper dimensions
            statusCtx.style.height = '280px';
            statusCtx.style.width = '100%';
            
            statusChart = new Chart(statusCtx, {
                type: 'pie',
                data: {
                    labels: dashboardData.status.labels,
                    datasets: [{
                        data: dashboardData.status.values,
                        backgroundColor: dashboardData.status.colors,
                        borderColor: theme === 'light' ? '#ffffff' : '#2d2d2d',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { 
                                color: textColor,
                                padding: 10,
                                font: { size: 10 }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating status chart:', error);
            showNoDataMessage('statusChart');
        }
    }
    
    // 4. Trends Chart (Line Chart) - Critical Fix
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx) {
        try {
            // Ensure canvas has proper dimensions
            trendsCtx.style.height = '280px';
            trendsCtx.style.width = '100%';
            
            trendsChart = new Chart(trendsCtx, {
                type: 'line',
                data: {
                    labels: dashboardData.trends.labels,
                    datasets: [
                        {
                            label: 'Applications',
                            data: dashboardData.trends.applications,
                            borderColor: '#79aec8',
                            backgroundColor: 'rgba(121, 174, 200, 0.2)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Acceptances',
                            data: dashboardData.trends.acceptances,
                            borderColor: '#10B981',
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'top',
                            labels: { 
                                color: textColor,
                                font: { size: 10 }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        y: { 
                            beginAtZero: true,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating trends chart:', error);
            showNoDataMessage('trendsChart');
        }
    }
}

// Show "No Data" message for failed charts
function showNoDataMessage(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const container = canvas.parentNode;
        container.innerHTML = '<p class="text-muted text-center mt-5" style="color: #79aec8;">No data available</p>';
    }
}

// Initialize dashboard when DOM is ready
function initDashboard() {
    // Setup theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const adminDashboard = document.getElementById('adminDashboard');
            const currentTheme = adminDashboard.classList.contains('light-mode') ? 'light' : 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
            localStorage.setItem('dashboardTheme', newTheme);
        });
    }
    
    // Load saved theme preference
    const savedTheme = localStorage.getItem('dashboardTheme') || 'dark';
    setTheme(savedTheme);
    
    // Initialize charts with proper timing
    if (window.Chart && dashboardData) {
        // Use requestAnimationFrame to ensure DOM is fully rendered
        requestAnimationFrame(() => {
            setTimeout(() => {
                initializeCharts();
            }, 100); // Small delay to ensure grid layout is calculated
        });
    } else {
        console.warn('Chart.js not loaded or dashboard data not available');
    }
}

// Export functions for global access
window.setDashboardData = function(data) {
    dashboardData = data;
};

window.initDashboard = initDashboard;
