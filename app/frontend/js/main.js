// Main application entry point
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all components
    window.ui.init();

    // Set up global error handling
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        window.ui.showNotification('An unexpected error occurred', 'error');
    });

    // Set up unhandled promise rejection handling
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        window.ui.showNotification('An unexpected error occurred', 'error');
    });

    // Initialize tooltips and other UI enhancements
    initializeTooltips();
    initializeKeyboardShortcuts();

    console.log('Data Wrangler application initialized successfully');
});

function initializeTooltips() {
    // Add tooltip functionality if needed
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.dataset.tooltip;
            document.body.appendChild(tooltip);

            const rect = e.target.getBoundingClientRect();
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
            tooltip.style.left = rect.left + (rect.width - tooltip.offsetWidth) / 2 + 'px';

            e.target._tooltip = tooltip;
        });

        element.addEventListener('mouseleave', (e) => {
            if (e.target._tooltip) {
                e.target._tooltip.remove();
                e.target._tooltip = null;
            }
        });
    });
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + S to save session
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            document.getElementById('save-session').click();
        }

        // Ctrl/Cmd + O to load session
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            document.getElementById('load-session').click();
        }
        
        // Ctrl/Cmd + U to upload file
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            document.getElementById('upload-btn').click();
        }

        // Escape to close modals or cancel operations
        if (e.key === 'Escape') {
            // Close any open modals or cancel operations
            const openModals = document.querySelectorAll('.modal.active');
            openModals.forEach(modal => modal.classList.remove('active'));
        }
    });
}

// Add CSS for tooltips and all profile page styling
const tooltipStyles = document.createElement('style');
tooltipStyles.textContent = `
.tooltip {
    position: absolute;
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    pointer-events: none;
    white-space: nowrap;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    z-index: 1000;
    transform: translateX(400px);
    transition: transform 0.3s ease;
    max-width: 300px;
}

.notification.show {
    transform: translateX(0);
}

.notification-success {
    background-color: #10b981;
}

.notification-error {
    background-color: #ef4444;
}

.notification-warning {
    background-color: #f59e0b;
}

.notification-info {
    background-color: #3b82f6;
}

/* --- NEW: Data Profile Page Glassmorphism Styling --- */

/* Main container for the profile report */
#profile-content {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    padding: 2rem;
}

/* Container for top stats (Total Rows, etc.) */
.profile-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0 2rem 0; /* Add more margin at the bottom */
}

/* Individual stat bubble (Total Rows, etc.) */
.stat-item {
    background-color: rgba(255, 255, 255, 0.25);
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.stat-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

/* Container for score cards (Overall, Completeness, etc.) */
.score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

/* Individual score card */
.score-item {
    text-align: center;
    background-color: rgba(255, 255, 255, 0.25);
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.score-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.score-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

.score-value {
    font-size: 1.5rem;
    font-weight: bold;
}

.score-excellent { color: #10b981; }
.score-good { color: #3b82f6; }
.score-fair { color: #f59e0b; }
.score-poor { color: #ef4444; }

/* PII Warning Box */
.pii-warning {
    /* Yellow-tinted glass */
    background: rgba(254, 243, 199, 0.5); /* #fef3c7 with alpha */
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border: 1px solid rgba(245, 158, 11, 0.5); /* #f59e0b with alpha */
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin: 2rem 0;
}
.pii-warning h3 {
    color: #92400e;
    margin-bottom: 0.5rem;
}
/* FIX: Pull the bullet points inside the container */
.pii-warning ul {
    margin: 0.5rem 0 0 0;
    padding-left: 1.5rem; /* Indent the list */
    list-style-position: outside; /* Ensure bullets are aligned */
}
.pii-warning li {
    margin-bottom: 0.25rem;
}

/* Recommendations Box */
.recommendations {
    /* Neutral/Blue-tinted glass */
    background: rgba(219, 234, 254, 0.4); /* #dbeafe with alpha */
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border: 1px solid rgba(59, 130, 246, 0.4); /* #3b82f6 with alpha */
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
}
.recommendations ul {
    margin: 0.5rem 0 0 0;
    padding-left: 1.5rem;
}
.recommendations li {
    margin: 0.5rem 0;
}
`;
document.head.appendChild(tooltipStyles);