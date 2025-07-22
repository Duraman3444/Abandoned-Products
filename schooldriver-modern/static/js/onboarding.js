/**
 * User Onboarding and Help System for SchoolDriver Modern
 * Provides guided tours, tooltips, and contextual help for new users
 */

class OnboardingManager {
    constructor() {
        this.currentStep = 0;
        this.tourSteps = [];
        this.isActive = false;
        this.overlay = null;
        this.helpPanel = null;
        this.init();
    }

    init() {
        this.createHelpButton();
        this.checkFirstTimeUser();
        this.setupKeyboardShortcuts();
    }

    /**
     * Create floating help button
     */
    createHelpButton() {
        const helpBtn = document.createElement('button');
        helpBtn.id = 'help-button';
        helpBtn.className = 'btn btn-primary position-fixed';
        helpBtn.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 1050;
            border-radius: 50%;
            width: 56px;
            height: 56px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        helpBtn.innerHTML = '<i class="bi bi-question-lg" aria-hidden="true"></i>';
        helpBtn.setAttribute('aria-label', 'Open help menu');
        helpBtn.setAttribute('title', 'Need help? Click for assistance (Press ? for keyboard shortcuts)');
        
        helpBtn.addEventListener('click', () => this.showHelpMenu());
        document.body.appendChild(helpBtn);
    }

    /**
     * Check if this is a first-time user and offer onboarding
     */
    checkFirstTimeUser() {
        const hasVisited = localStorage.getItem('schooldriver_onboarding_completed');
        if (!hasVisited) {
            // Delay to ensure page is fully loaded
            setTimeout(() => {
                this.showWelcomeModal();
            }, 1000);
        }
    }

    /**
     * Show welcome modal for new users
     */
    showWelcomeModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'welcome-modal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'welcome-modal-title');
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark text-light">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title text-info" id="welcome-modal-title">
                            <i class="bi bi-mortarboard me-2"></i>Welcome to SchoolDriver Modern!
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6 class="text-info">Get Started Quickly</h6>
                                <p>We've designed SchoolDriver Modern to be intuitive, but let us show you around to get the most out of your experience.</p>
                                
                                <h6 class="text-info mt-4">What you can do:</h6>
                                <ul class="list-unstyled">
                                    <li class="mb-2"><i class="bi bi-speedometer2 text-teal me-2"></i><strong>Dashboard:</strong> Quick overview of grades, assignments, and schedule</li>
                                    <li class="mb-2"><i class="bi bi-bar-chart text-teal me-2"></i><strong>Grades:</strong> Detailed view of course performance and GPA</li>
                                    <li class="mb-2"><i class="bi bi-clipboard2-check text-teal me-2"></i><strong>Assignments:</strong> Track upcoming and completed work</li>
                                    <li class="mb-2"><i class="bi bi-calendar3 text-teal me-2"></i><strong>Schedule:</strong> View class times and teacher contacts</li>
                                    <li class="mb-2"><i class="bi bi-person text-teal me-2"></i><strong>Profile:</strong> Manage personal information and settings</li>
                                </ul>
                                
                                <div class="alert alert-info border-info">
                                    <i class="bi bi-lightbulb me-2"></i>
                                    <strong>Tip:</strong> Use the help button (?) in the bottom-right corner anytime you need assistance!
                                </div>
                            </div>
                            <div class="col-md-4 text-center">
                                <div class="mb-3">
                                    <i class="bi bi-mortarboard text-info" style="font-size: 4rem;"></i>
                                </div>
                                <div class="d-grid gap-2">
                                    <button type="button" class="btn btn-info" onclick="onboarding.startTour()">
                                        <i class="bi bi-play-circle me-2"></i>Start Guided Tour
                                    </button>
                                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal" onclick="onboarding.skipOnboarding()">
                                        <i class="bi bi-skip-forward me-2"></i>Skip Tour
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * Start the guided tour
     */
    startTour() {
        const welcomeModal = bootstrap.Modal.getInstance(document.getElementById('welcome-modal'));
        if (welcomeModal) {
            welcomeModal.hide();
        }

        // Define tour steps based on current page
        this.tourSteps = this.getTourStepsForPage();
        
        if (this.tourSteps.length === 0) {
            this.showMessage('Tour not available on this page. Please visit the Dashboard to start the tour.', 'info');
            return;
        }

        this.currentStep = 0;
        this.isActive = true;
        this.createOverlay();
        this.showStep(0);
    }

    /**
     * Get tour steps based on current page
     */
    getTourStepsForPage() {
        const path = window.location.pathname;
        
        if (path.includes('dashboard')) {
            return [
                {
                    target: '.sidebar .nav-link[href*="dashboard"]',
                    title: 'Navigation Menu',
                    content: 'Use this sidebar to navigate between different sections of your student portal.',
                    position: 'right'
                },
                {
                    target: '[data-tour="gpa-cards"]',
                    title: 'Academic Overview',
                    content: 'Here you can see your current GPA and academic performance at a glance.',
                    position: 'bottom'
                },
                {
                    target: '[data-tour="upcoming-assignments"]',
                    title: 'Upcoming Assignments',
                    content: 'Stay on top of your coursework with this list of upcoming assignments and due dates.',
                    position: 'top'
                },
                {
                    target: '[data-tour="today-schedule"]',
                    title: 'Today\'s Schedule',
                    content: 'View your classes for today, including times and classroom locations.',
                    position: 'left'
                }
            ];
        } else if (path.includes('grades')) {
            return [
                {
                    target: 'select[name="year"]',
                    title: 'School Year Filter',
                    content: 'Use this dropdown to view grades from different school years.',
                    position: 'bottom'
                },
                {
                    target: '.course-grade-card:first-child',
                    title: 'Course Grades',
                    content: 'Each card shows your current grade, progress, and breakdown by category for each course.',
                    position: 'right'
                }
            ];
        }
        
        return [];
    }

    /**
     * Create overlay for tour
     */
    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.id = 'tour-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(this.overlay);
    }

    /**
     * Show specific tour step
     */
    showStep(stepIndex) {
        if (stepIndex >= this.tourSteps.length) {
            this.endTour();
            return;
        }

        const step = this.tourSteps[stepIndex];
        const target = document.querySelector(step.target);
        
        if (!target) {
            // Skip missing elements
            this.showStep(stepIndex + 1);
            return;
        }

        // Highlight target element
        this.highlightElement(target);
        
        // Create and show tooltip
        this.showTooltip(target, step, stepIndex);
    }

    /**
     * Highlight target element
     */
    highlightElement(element) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });

        element.classList.add('tour-highlight');
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add CSS for highlight if not already added
        if (!document.getElementById('tour-styles')) {
            const style = document.createElement('style');
            style.id = 'tour-styles';
            style.textContent = `
                .tour-highlight {
                    position: relative;
                    z-index: 10001 !important;
                    box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.8) !important;
                    border-radius: 4px;
                }
                .tour-tooltip {
                    position: absolute;
                    background: #1a1a1a;
                    color: white;
                    padding: 16px;
                    border-radius: 8px;
                    max-width: 300px;
                    z-index: 10002;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    border: 1px solid #444;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Show tooltip for current step
     */
    showTooltip(target, step, stepIndex) {
        // Remove existing tooltip
        const existingTooltip = document.querySelector('.tour-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }

        const tooltip = document.createElement('div');
        tooltip.className = 'tour-tooltip';
        tooltip.innerHTML = `
            <div class="mb-2">
                <strong class="text-info">${step.title}</strong>
                <span class="text-muted ms-2">(${stepIndex + 1}/${this.tourSteps.length})</span>
            </div>
            <p class="mb-3">${step.content}</p>
            <div class="d-flex justify-content-between align-items-center">
                <button class="btn btn-sm btn-outline-secondary" onclick="onboarding.endTour()">
                    <i class="bi bi-x me-1"></i>Skip
                </button>
                <div>
                    ${stepIndex > 0 ? '<button class="btn btn-sm btn-outline-info me-2" onclick="onboarding.previousStep()"><i class="bi bi-arrow-left me-1"></i>Back</button>' : ''}
                    <button class="btn btn-sm btn-info" onclick="onboarding.nextStep()">
                        ${stepIndex === this.tourSteps.length - 1 ? '<i class="bi bi-check me-1"></i>Finish' : '<i class="bi bi-arrow-right me-1"></i>Next'}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(tooltip);
        this.positionTooltip(tooltip, target, step.position);
    }

    /**
     * Position tooltip relative to target
     */
    positionTooltip(tooltip, target, position) {
        const targetRect = target.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = targetRect.top - tooltipRect.height - 10;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = targetRect.bottom + 10;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.left - tooltipRect.width - 10;
                break;
            case 'right':
            default:
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.right + 10;
                break;
        }
        
        // Ensure tooltip stays within viewport
        top = Math.max(10, Math.min(top, window.innerHeight - tooltipRect.height - 10));
        left = Math.max(10, Math.min(left, window.innerWidth - tooltipRect.width - 10));
        
        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
    }

    /**
     * Navigate to next step
     */
    nextStep() {
        this.currentStep++;
        this.showStep(this.currentStep);
    }

    /**
     * Navigate to previous step
     */
    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    /**
     * End the tour
     */
    endTour() {
        this.isActive = false;
        
        // Remove overlay and tooltip
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        
        const tooltip = document.querySelector('.tour-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
        
        // Remove highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Mark onboarding as completed
        localStorage.setItem('schooldriver_onboarding_completed', 'true');
        
        this.showMessage('Tour completed! Use the help button anytime you need assistance.', 'success');
    }

    /**
     * Skip onboarding entirely
     */
    skipOnboarding() {
        localStorage.setItem('schooldriver_onboarding_completed', 'true');
        this.showMessage('You can always restart the tour from the help menu.', 'info');
    }

    /**
     * Show help menu
     */
    showHelpMenu() {
        const menu = document.createElement('div');
        menu.className = 'help-menu position-fixed bg-dark text-light p-3 rounded shadow';
        menu.style.cssText = `
            bottom: 80px;
            right: 20px;
            z-index: 1051;
            min-width: 250px;
            border: 1px solid #444;
        `;
        
        menu.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 text-info"><i class="bi bi-question-circle me-2"></i>Help & Support</h6>
                <button class="btn-close btn-close-white btn-sm" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="d-grid gap-2">
                <button class="btn btn-sm btn-outline-info" onclick="onboarding.startTour(); this.parentElement.parentElement.remove();">
                    <i class="bi bi-play-circle me-2"></i>Start Tour
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="onboarding.showKeyboardShortcuts()">
                    <i class="bi bi-keyboard me-2"></i>Keyboard Shortcuts
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="onboarding.showFeatureGuide()">
                    <i class="bi bi-book me-2"></i>Feature Guide
                </button>
                <hr class="my-2">
                <small class="text-muted">
                    <i class="bi bi-info-circle me-1"></i>
                    Press <kbd>?</kbd> for keyboard shortcuts
                </small>
            </div>
        `;
        
        document.body.appendChild(menu);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (menu.parentElement) {
                menu.remove();
            }
        }, 10000);
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch (e.key) {
                case '?':
                    e.preventDefault();
                    this.showKeyboardShortcuts();
                    break;
                case 'Escape':
                    if (this.isActive) {
                        this.endTour();
                    }
                    break;
            }
        });
    }

    /**
     * Show keyboard shortcuts modal
     */
    showKeyboardShortcuts() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content bg-dark text-light">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title text-info">
                            <i class="bi bi-keyboard me-2"></i>Keyboard Shortcuts
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-6">
                                <h6 class="text-info">Navigation</h6>
                                <div class="mb-2"><kbd>1</kbd> Dashboard</div>
                                <div class="mb-2"><kbd>2</kbd> Grades</div>
                                <div class="mb-2"><kbd>3</kbd> Assignments</div>
                                <div class="mb-2"><kbd>4</kbd> Schedule</div>
                                <div class="mb-2"><kbd>5</kbd> Profile</div>
                            </div>
                            <div class="col-6">
                                <h6 class="text-info">General</h6>
                                <div class="mb-2"><kbd>?</kbd> Help menu</div>
                                <div class="mb-2"><kbd>Esc</kbd> Close tour/modal</div>
                                <div class="mb-2"><kbd>Tab</kbd> Navigate elements</div>
                                <div class="mb-2"><kbd>Enter</kbd> Activate links</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }

    /**
     * Show feature guide
     */
    showFeatureGuide() {
        this.showMessage('Feature guide coming soon! For now, use the guided tour to learn about available features.', 'info');
    }

    /**
     * Show temporary message
     */
    showMessage(text, type = 'info') {
        if (window.accessibility && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader(text);
        }
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 1052; max-width: 400px;';
        alert.innerHTML = `
            ${text}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize onboarding when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.onboarding = new OnboardingManager();
});

// Add keyboard shortcuts for navigation
document.addEventListener('keydown', function(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    const shortcuts = {
        '1': '/student/dashboard/',
        '2': '/student/grades/',
        '3': '/student/assignments/',
        '4': '/student/schedule/',
        '5': '/student/profile/'
    };
    
    if (shortcuts[e.key]) {
        e.preventDefault();
        window.location.href = shortcuts[e.key];
    }
});
