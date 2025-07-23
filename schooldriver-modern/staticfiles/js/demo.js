/**
 * Demo Page JavaScript
 * Handles Chart.js initialization and interactive demo features
 */

let gpaChart;

/**
 * Initialize demo page with chart data
 */
function initializeDemoPage(gpaData) {
    initializeGPAChart(gpaData);
    initializeResponsiveCarousel();
    initializeDemoSearch();
}

/**
 * Initialize GPA analytics chart
 */
function initializeGPAChart(data) {
    const ctx = document.getElementById('gpaChart');
    if (!ctx) return;

    gpaChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'GPA by Grade Level',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 4.0,
                    min: 0,
                    ticks: {
                        stepSize: 0.5,
                        maxTicksLimit: 9,
                        callback: function(value) {
                            return value.toFixed(1);
                        }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutBounce'
            }
        }
    });
}

/**
 * Initialize responsive design carousel
 */
function initializeResponsiveCarousel() {
    const carousel = document.getElementById('responsiveCarousel');
    if (carousel) {
        // Auto-cycle through responsive views
        setInterval(() => {
            const nextButton = carousel.querySelector('.carousel-control-next');
            if (nextButton) {
                nextButton.click();
            }
        }, 3000);
    }
}

/**
 * Initialize demo search functionality
 */
function initializeDemoSearch() {
    const searchInput = document.getElementById('demoSearchInput');
    if (searchInput) {
        // Add sample suggestions
        const suggestions = ['Emma Johnson', 'Mathematics', 'Grade 5', 'Language Arts', 'John Smith'];
        let currentSuggestion = 0;
        
        // Cycle through suggestions as placeholder
        setInterval(() => {
            searchInput.placeholder = `Search: "${suggestions[currentSuggestion]}"...`;
            currentSuggestion = (currentSuggestion + 1) % suggestions.length;
        }, 2000);
        
        // Handle enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performDemoSearch();
            }
        });
    }
}

/**
 * Perform demo search - opens in new tab
 */
function performDemoSearch() {
    const searchInput = document.getElementById('demoSearchInput');
    const query = searchInput.value.trim();
    
    if (query) {
        // Open search in new tab
        window.open(`/search/?q=${encodeURIComponent(query)}`, '_blank');
    } else {
        // Use placeholder text for demo
        const placeholderQuery = searchInput.placeholder.match(/"([^"]+)"/);
        if (placeholderQuery) {
            window.open(`/search/?q=${encodeURIComponent(placeholderQuery[1])}`, '_blank');
        }
    }
}

/**
 * Handle API endpoint testing
 */
function testAPIEndpoint(url) {
    // Open API endpoint in new tab
    window.open(url, '_blank');
}

/**
 * Animate counter numbers on scroll
 */
function animateCounters() {
    const counters = document.querySelectorAll('.demo-hero h3');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.textContent.replace(/\D/g, ''));
                let current = 0;
                
                const increment = target / 30;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                        counter.textContent = target + (counter.textContent.includes('+') ? '+' : '');
                    } else {
                        counter.textContent = Math.floor(current) + (counter.textContent.includes('+') ? '+' : '');
                    }
                }, 50);
                
                observer.unobserve(counter);
            }
        });
    });
    
    counters.forEach(counter => observer.observe(counter));
}

/**
 * Add hover effects to feature cards
 */
function initializeFeatureCards() {
    const cards = document.querySelectorAll('.feature-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/**
 * Initialize demo page when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    animateCounters();
    initializeFeatureCards();
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

/**
 * Cleanup function for page unload
 */
window.addEventListener('beforeunload', function() {
    if (gpaChart) {
        gpaChart.destroy();
    }
});
