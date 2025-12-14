/**
 * TherapyTrack - Main Application JavaScript
 * Handles API calls, authentication, UI interactions, and utilities
 */

// API Base URL
const API_BASE = '/api';

// ==================== Utility Functions ====================

/**
 * Show toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of toast: success, error, warning, info
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-times-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Format date to readable string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Format date for input fields
 * @param {Date} date - Date object
 * @returns {string} YYYY-MM-DD format
 */
function formatDateForInput(date = new Date()) {
    return date.toISOString().split('T')[0];
}

/**
 * Calculate age from birthdate
 * @param {string} birthdate - Birth date string
 * @returns {number} Age in years
 */
function calculateAge(birthdate) {
    const today = new Date();
    const birth = new Date(birthdate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    return age;
}

/**
 * Debounce function for search inputs
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== API Functions ====================

/**
 * Make authenticated API request
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise} API response
 */
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, mergedOptions);
        
        if (response.status === 401) {
            localStorage.clear();
            window.location.href = '/login';
            return null;
        }

        return response;
    } catch (error) {
        console.error('API Request Error:', error);
        showToast('Network error. Please try again.', 'error');
        throw error;
    }
}

/**
 * Register a new user
 * @param {string} userType - 'doctor' or 'parent'
 * @param {object} userData - User registration data
 * @returns {Promise} Registration result
 */
async function registerUser(userType, userData) {
    const endpoint = userType === 'doctor' ? '/auth/register-doctor' : '/auth/register-parent';
    
    const response = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(userData)
    });

    if (response && response.ok) {
        const data = await response.json();
        showToast('Registration successful! Please login.', 'success');
        return data;
    } else if (response) {
        const error = await response.json();
        showToast(error.detail || 'Registration failed', 'error');
        throw new Error(error.detail);
    }
}

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {string} userType - 'doctor' or 'parent'
 * @returns {Promise} Login result
 */
async function loginUser(email, password, userType) {
    const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, user_type: userType })
    });

    if (response && response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userType', data.user_type);
        localStorage.setItem('userName', data.name);
        localStorage.setItem('userId', data.user_id);
        showToast('Login successful!', 'success');
        return data;
    } else if (response) {
        const error = await response.json();
        showToast(error.detail || 'Login failed', 'error');
        throw new Error(error.detail);
    }
}

/**
 * Logout current user
 */
function logout() {
    localStorage.clear();
    showToast('Logged out successfully', 'success');
    setTimeout(() => {
        window.location.href = '/login';
    }, 500);
}

/**
 * Get current user info
 * @returns {object} User info from localStorage
 */
function getCurrentUser() {
    return {
        token: localStorage.getItem('token'),
        userType: localStorage.getItem('userType'),
        userName: localStorage.getItem('userName'),
        userId: localStorage.getItem('userId')
    };
}

/**
 * Check if user is authenticated
 * @returns {boolean} Authentication status
 */
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// ==================== Child Management ====================

/**
 * Create a new child profile
 * @param {object} childData - Child profile data
 * @returns {Promise} Created child data
 */
async function createChild(childData) {
    const response = await apiRequest('/doctor/create-child', {
        method: 'POST',
        body: JSON.stringify(childData)
    });

    if (response && response.ok) {
        const data = await response.json();
        showToast('Child profile created successfully!', 'success');
        return data;
    } else if (response) {
        const error = await response.json();
        showToast(error.detail || 'Failed to create child profile', 'error');
        throw new Error(error.detail);
    }
}

/**
 * Get all children for current doctor
 * @returns {Promise} Array of children
 */
async function getChildren() {
    const response = await apiRequest('/doctor/children');
    
    if (response && response.ok) {
        return await response.json();
    }
    return [];
}

/**
 * Get child by ID
 * @param {string} childId - Child ID
 * @returns {Promise} Child data
 */
async function getChild(childId) {
    const response = await apiRequest(`/child/${childId}`);
    
    if (response && response.ok) {
        return await response.json();
    }
    return null;
}

// ==================== Therapy Session Management ====================

/**
 * Add a new therapy log
 * @param {object} logData - Therapy session data
 * @returns {Promise} Created log data
 */
async function addTherapyLog(logData) {
    const response = await apiRequest('/therapy/add-log', {
        method: 'POST',
        body: JSON.stringify(logData)
    });

    if (response && response.ok) {
        const data = await response.json();
        showToast('Therapy session saved successfully!', 'success');
        return data;
    } else if (response) {
        const error = await response.json();
        showToast(error.detail || 'Failed to save therapy session', 'error');
        throw new Error(error.detail);
    }
}

/**
 * Get therapy logs for a child
 * @param {string} childId - Child ID
 * @returns {Promise} Array of therapy logs
 */
async function getTherapyLogs(childId) {
    const response = await apiRequest(`/therapy/logs/${childId}`);
    
    if (response && response.ok) {
        return await response.json();
    }
    return [];
}

// ==================== Reports ====================

/**
 * Get weekly report for a child
 * @param {string} childId - Child ID
 * @returns {Promise} Weekly report data
 */
async function getWeeklyReport(childId) {
    const response = await apiRequest(`/reports/weekly/${childId}`);
    
    if (response && response.ok) {
        return await response.json();
    }
    return null;
}

/**
 * Get monthly report for a child
 * @param {string} childId - Child ID
 * @returns {Promise} Monthly report data
 */
async function getMonthlyReport(childId) {
    const response = await apiRequest(`/reports/monthly/${childId}`);
    
    if (response && response.ok) {
        return await response.json();
    }
    return null;
}

// ==================== UI Helpers ====================

/**
 * Initialize tooltips
 */
function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
        });
        
        el.addEventListener('mouseleave', function() {
            document.querySelectorAll('.tooltip').forEach(t => t.remove());
        });
    });
}

/**
 * Initialize form validation
 * @param {HTMLFormElement} form - Form element
 */
function initFormValidation(form) {
    form.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

/**
 * Validate a form field
 * @param {HTMLElement} field - Field to validate
 * @returns {boolean} Validation result
 */
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';

    if (field.required && !value) {
        isValid = false;
        message = 'This field is required';
    } else if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email address';
        }
    } else if (field.minLength && value.length < field.minLength) {
        isValid = false;
        message = `Minimum ${field.minLength} characters required`;
    }

    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        // Show error message
        let errorEl = field.parentElement.querySelector('.field-error');
        if (!errorEl) {
            errorEl = document.createElement('span');
            errorEl.className = 'field-error';
            field.parentElement.appendChild(errorEl);
        }
        errorEl.textContent = message;
    }

    return isValid;
}

/**
 * Toggle password visibility
 * @param {string} inputId - Password input ID
 * @param {HTMLElement} toggleBtn - Toggle button element
 */
function togglePassword(inputId, toggleBtn) {
    const input = document.getElementById(inputId);
    const icon = toggleBtn.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

/**
 * Handle dropdown menus
 */
function initDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.nextElementSibling;
            dropdown.classList.toggle('show');
        });
    });

    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
}

/**
 * Handle modal dialogs
 */
function initModals() {
    // Open modal
    document.querySelectorAll('[data-modal]').forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    // Close modal
    document.querySelectorAll('.modal-close, .modal-backdrop').forEach(closer => {
        closer.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.classList.remove('show');
                document.body.style.overflow = '';
            }
        });
    });

    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(modal => {
                modal.classList.remove('show');
                document.body.style.overflow = '';
            });
        }
    });
}

/**
 * Animate elements on scroll
 */
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1
    });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Handle sidebar toggle for mobile
 */
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    
    if (toggle && sidebar) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
}

// ==================== Chart Helpers ====================

/**
 * Get chart default options
 * @returns {object} Default chart options
 */
function getChartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    font: {
                        family: "'Inter', sans-serif"
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0,0,0,0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        }
    };
}

/**
 * Generate gradient for charts
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {string} color1 - Start color
 * @param {string} color2 - End color
 * @returns {CanvasGradient} Gradient object
 */
function createChartGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

// ==================== Rating Helpers ====================

/**
 * Convert rating enum to numeric value
 * @param {string} rating - Rating string (good, average, no_improvement)
 * @returns {number} Numeric value (3, 2, 1)
 */
function ratingToNumber(rating) {
    const ratings = {
        'good': 3,
        'average': 2,
        'no_improvement': 1
    };
    return ratings[rating] || 0;
}

/**
 * Convert numeric value to percentage
 * @param {number} value - Rating value (1-3)
 * @returns {number} Percentage (0-100)
 */
function ratingToPercentage(value) {
    return Math.round((value / 3) * 100);
}

/**
 * Calculate average domain score
 * @param {object} domainRatings - Object with rating values
 * @returns {number} Average percentage
 */
function calculateDomainAverage(domainRatings) {
    const values = Object.values(domainRatings);
    if (values.length === 0) return 0;
    
    const sum = values.reduce((acc, rating) => acc + ratingToNumber(rating), 0);
    return ratingToPercentage(sum / values.length);
}

// ==================== Initialization ====================

/**
 * Initialize all UI components
 */
function initApp() {
    initTooltips();
    initDropdowns();
    initModals();
    initScrollAnimations();
    initSidebar();
    
    // Set current date for date inputs
    document.querySelectorAll('input[type="date"]').forEach(input => {
        if (!input.value) {
            input.value = formatDateForInput();
        }
    });

    // Initialize forms
    document.querySelectorAll('form').forEach(form => {
        initFormValidation(form);
    });

    console.log('TherapyTrack App Initialized');
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);

// Export functions for global use
window.TherapyTrack = {
    showToast,
    formatDate,
    formatDateForInput,
    calculateAge,
    debounce,
    apiRequest,
    registerUser,
    loginUser,
    logout,
    getCurrentUser,
    isAuthenticated,
    createChild,
    getChildren,
    getChild,
    addTherapyLog,
    getTherapyLogs,
    getWeeklyReport,
    getMonthlyReport,
    togglePassword,
    validateField,
    getChartDefaults,
    createChartGradient,
    ratingToNumber,
    ratingToPercentage,
    calculateDomainAverage
};
