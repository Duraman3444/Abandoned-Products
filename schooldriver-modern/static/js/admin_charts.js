// Admin Dashboard Charts - External JavaScript
// Fixes chart rendering issues by ensuring proper initialization timing

// Simple data labels plugin for Chart.js v4
const dataLabelsPlugin = {
    id: 'dataLabels',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        ctx.save();
        
        chart.data.datasets.forEach((dataset, datasetIndex) => {
            const meta = chart.getDatasetMeta(datasetIndex);
            if (!meta.hidden) {
                meta.data.forEach((element, index) => {
                    const value = dataset.data[index];
                    if (value > 0) {
                        ctx.fillStyle = '#ffffff';
                        ctx.font = 'bold 12px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        
                        let text, x, y;
                        
                        // Check if it's horizontal bar chart (pipeline)
                        if (chart.config.options.indexAxis === 'y') {
                            text = value + ' applicants';
                            x = element.x - 40;
                            y = element.y;
                        } else {
                            // Vertical bar chart (documents)
                            text = value + '%';
                            x = element.x;
                            y = element.y - 10;
                        }
                        
                        ctx.fillText(text, x, y);
                    }
                });
            }
        });
        
        ctx.restore();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Wait one frame so CSS has applied and layout is stable
    requestAnimationFrame(initializeAdminCharts);
});

// Chart instances
let pipelineChart, documentsChart, statusChart, trendsChart;

function initializeAdminCharts() {
    const data = window.dashboardData;
    if (!data) {
        console.error('Dashboard data not available');
        return;
    }
    
    const theme = document.getElementById('adminDashboard')
                    .classList.contains('light-mode') ? 'light' : 'dark';
    
    // Force canvas dimensions before initialization
    forceCanvasDimensions();
    
    // Small delay to ensure layout is calculated
    setTimeout(() => {
        buildPipelineChart(data, theme);
        buildDocumentsChart(data, theme);
        buildStatusChart(data, theme);
        buildTrendsChart(data, theme);
        
        // Force a refresh to ensure legends are rendered
        setTimeout(() => {
            if (pipelineChart) pipelineChart.update('active');
            if (documentsChart) documentsChart.update('active');
        }, 100);
    }, 150);
}

function forceCanvasDimensions() {
    const canvases = ['pipelineChart', 'documentsChart', 'statusChart', 'trendsChart'];
    canvases.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            const container = canvas.closest('.chart-container');
            if (container) {
                // Force container dimensions - extra height for legends
                if (id === 'pipelineChart' || id === 'documentsChart') {
                    container.style.minHeight = '380px';
                    container.style.height = '380px';
                } else {
                    container.style.minHeight = '320px';
                    container.style.height = '320px';
                }
            }
            // Force canvas dimensions
            canvas.style.width = '100%';
            if (id === 'pipelineChart' || id === 'documentsChart') {
                canvas.style.height = '340px';
                canvas.height = 340;
            } else {
                canvas.style.height = '280px';
                canvas.height = 280;
            }
            canvas.width = canvas.offsetWidth;
        }
    });
}

function getThemeColors(theme) {
    const textColor = theme === 'light' ? '#333333' : '#e0e0e0';
    const gridColor = theme === 'light' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)';
    return { textColor, gridColor };
}

function buildPipelineChart(data, theme) {
    const canvas = document.getElementById('pipelineChart');
    if (!canvas) return;
    
    const dataset = data.pipeline;
    if (!dataset.values || dataset.values.length === 0 || dataset.values.every(v => v === 0)) {
        canvas.closest('.chart-container').innerHTML = 
            '<h3 style="color: #79aec8; margin-bottom: 10px;">Admission Pipeline</h3>' +
            '<p class="text-muted text-center mt-5">No pipeline data available</p>';
        return;
    }
    
    const { textColor, gridColor } = getThemeColors(theme);
    
    if (pipelineChart) pipelineChart.destroy();
    
    pipelineChart = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dataset.labels,
            datasets: [{
                label: 'Applicants',
                data: dataset.values,
                backgroundColor: dataset.colors,
                borderColor: dataset.colors.map(color => color + 'CC'),
                borderWidth: 1
            }]
        },
        plugins: [dataLabelsPlugin],
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: true,
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                const labels = data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value} applicants)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].backgroundColor[i],
                                        lineWidth: 0,
                                        hidden: false,
                                        index: i
                                    };
                                });
                                console.log('Pipeline legend labels generated:', labels);
                                return labels;
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' applicants';
                        }
                    }
                }
            },
            scales: {
                x: { 
                    beginAtZero: true,
                    ticks: { 
                        color: textColor,
                        callback: function(value) {
                            return value + ' applicants';
                        }
                    },
                    grid: { color: gridColor }
                },
                y: {
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

function buildDocumentsChart(data, theme) {
    const canvas = document.getElementById('documentsChart');
    if (!canvas) return;
    
    const dataset = data.documents;
    if (!dataset.completion_rates || dataset.completion_rates.length === 0 || 
        dataset.completion_rates.every(v => v === 0)) {
        canvas.closest('.chart-container').innerHTML = 
            '<h3 style="color: #79aec8; margin-bottom: 10px;">Document Completion</h3>' +
            '<p class="text-muted text-center mt-5">No document data available</p>';
        return;
    }
    
    const { textColor, gridColor } = getThemeColors(theme);
    
    if (documentsChart) documentsChart.destroy();
    
    documentsChart = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dataset.labels,
            datasets: [{
                label: 'Completion Rate (%)',
                data: dataset.completion_rates,
                backgroundColor: dataset.colors,
                borderColor: dataset.colors.map(color => color + 'CC'),
                borderWidth: 1
            }]
        },
        plugins: [dataLabelsPlugin],
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: true,
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                const labels = data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].backgroundColor[i],
                                        lineWidth: 0,
                                        hidden: false,
                                        index: i
                                    };
                                });
                                console.log('Documents legend labels generated:', labels);
                                return labels;
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + '% completion rate';
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: textColor,
                        maxRotation: 45,
                        minRotation: 45
                    },
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
}

function buildStatusChart(data, theme) {
    const canvas = document.getElementById('statusChart');
    if (!canvas) return;
    
    const dataset = data.status;
    if (!dataset.values || dataset.values.length === 0 || dataset.values.every(v => v === 0)) {
        canvas.closest('.chart-container').innerHTML = 
            '<h3 style="color: #79aec8; margin-bottom: 10px;">Status Distribution</h3>' +
            '<p class="text-muted text-center mt-5">No status data available</p>';
        return;
    }
    
    const { textColor } = getThemeColors(theme);
    
    if (statusChart) statusChart.destroy();
    
    statusChart = new Chart(canvas.getContext('2d'), {
        type: 'pie',
        data: {
            labels: dataset.labels,
            datasets: [{
                data: dataset.values,
                backgroundColor: dataset.colors,
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
}

function buildTrendsChart(data, theme) {
    const canvas = document.getElementById('trendsChart');
    if (!canvas) return;
    
    const dataset = data.trends;
    if (!dataset.applications || dataset.applications.length === 0 || 
        dataset.applications.every(v => v === 0)) {
        canvas.closest('.chart-container').innerHTML = 
            '<h3 style="color: #79aec8; margin-bottom: 10px;">Monthly Trends</h3>' +
            '<p class="text-muted text-center mt-5">No trends data available</p>';
        return;
    }
    
    const { textColor, gridColor } = getThemeColors(theme);
    
    if (trendsChart) trendsChart.destroy();
    
    trendsChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: dataset.labels,
            datasets: [
                {
                    label: 'Applications',
                    data: dataset.applications,
                    borderColor: '#79aec8',
                    backgroundColor: 'rgba(121, 174, 200, 0.2)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Acceptances',
                    data: dataset.acceptances,
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
}

// Theme update function
function updateAdminChartsTheme(theme) {
    if (window.dashboardData) {
        buildPipelineChart(window.dashboardData, theme);
        buildDocumentsChart(window.dashboardData, theme);
        buildStatusChart(window.dashboardData, theme);
        buildTrendsChart(window.dashboardData, theme);
    }
}

// Export for global access
window.updateAdminChartsTheme = updateAdminChartsTheme;
