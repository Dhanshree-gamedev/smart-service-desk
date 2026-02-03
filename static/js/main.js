/**
 * Smart Service Desk - Client-side JavaScript
 * Handles form validation, interactions, and dynamic UI updates
 */

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    initFlashMessages();

    // Initialize form validation
    initFormValidation();

    // Initialize filter interactions
    initFilters();

    // Initialize tooltips
    initTooltips();
});

/**
 * Flash Messages Auto-Dismiss
 */
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        // Add close button functionality
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                dismissAlert(alert);
            });
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            dismissAlert(alert);
        }, 5000);
    });
}

function dismissAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-10px)';
    setTimeout(() => {
        alert.remove();
    }, 300);
}

/**
 * Form Validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            let isValid = true;

            // Clear previous errors
            form.querySelectorAll('.form-error').forEach(el => el.remove());
            form.querySelectorAll('.form-control.error').forEach(el => {
                el.classList.remove('error');
            });

            // Validate required fields
            form.querySelectorAll('[required]').forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    showFieldError(field, 'This field is required');
                }
            });

            // Validate email fields
            form.querySelectorAll('input[type="email"]').forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    isValid = false;
                    showFieldError(field, 'Please enter a valid email address');
                }
            });

            // Validate password confirmation
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                isValid = false;
                showFieldError(confirmPassword, 'Passwords do not match');
            }

            // Validate minimum length
            form.querySelectorAll('[data-minlength]').forEach(field => {
                const minLength = parseInt(field.dataset.minlength);
                if (field.value.length < minLength) {
                    isValid = false;
                    showFieldError(field, `Minimum ${minLength} characters required`);
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });

        // Real-time validation on input
        form.querySelectorAll('.form-control').forEach(field => {
            field.addEventListener('input', function () {
                this.classList.remove('error');
                const errorEl = this.parentNode.querySelector('.form-error');
                if (errorEl) errorEl.remove();
            });
        });
    });
}

function showFieldError(field, message) {
    field.classList.add('error');

    const errorEl = document.createElement('div');
    errorEl.className = 'form-error';
    errorEl.textContent = message;
    errorEl.style.cssText = 'color: var(--danger-600); font-size: 0.8125rem; margin-top: 0.25rem;';

    field.parentNode.appendChild(errorEl);
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Filter Interactions
 */
function initFilters() {
    const filterSelects = document.querySelectorAll('.filter-group select');

    filterSelects.forEach(select => {
        select.addEventListener('change', function () {
            const form = this.closest('form');
            if (form) {
                form.submit();
            } else {
                // Build URL with filter parameters
                const url = new URL(window.location.href);

                if (this.value) {
                    url.searchParams.set(this.name, this.value);
                } else {
                    url.searchParams.delete(this.name);
                }

                window.location.href = url.toString();
            }
        });
    });
}

/**
 * Tooltip Initialization
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', function () {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: var(--gray-900);
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 0.375rem;
                font-size: 0.75rem;
                z-index: 1000;
                pointer-events: none;
                animation: fadeIn 0.2s ease;
            `;

            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';

            this._tooltip = tooltip;
        });

        el.addEventListener('mouseleave', function () {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Confirm Dialog
 */
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

/**
 * Format Date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Copy to Clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Show Toast Notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        dismissAlert(toast);
    }, 3000);
}

/**
 * Add loading state to buttons
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `
            <svg class="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="4" stroke-opacity="0.25"></circle>
                <path d="M12 2C6.48 2 2 6.48 2 12" stroke-width="4" stroke-linecap="round"></path>
            </svg>
            Loading...
        `;
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText;
    }
}
