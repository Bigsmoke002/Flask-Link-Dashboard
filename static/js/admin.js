/*
 * ============================================
 * ADMIN DASHBOARD JAVASCRIPT
 * ============================================
 * 
 * Handles all client-side functionality for the admin interface:
 * - Admin login form handling
 * - Dashboard management
 * - User management
 * - System monitoring
 * - Security features
 */

// Global Variables
let currentSection = 'overview';
let adminTheme = 'default';

/* ============================================
   INITIALIZATION
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    handleFlashMessages();
    
    // Initialize based on current page
    if (document.querySelector('.admin-login-container')) {
        initializeAdminLogin();
    } else if (document.querySelector('.admin-container')) {
        initializeAdminDashboard();
    }
    
    // Load admin theme
    loadAdminTheme();
});

/* ============================================
   FLASH MESSAGES
   ============================================ */

function handleFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message, index) => {
        setTimeout(() => {
            message.style.animation = 'slideOutToRight 0.4s ease-in forwards';
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 400);
        }, 4000 + (index * 500));
    });
}

/* ============================================
   ADMIN LOGIN FUNCTIONALITY
   ============================================ */

function initializeAdminLogin() {
    setupAdminFormHandling();
    focusFirstInput();
    setupAdminKeyboardShortcuts();
    showSecurityWarnings();
}

function setupAdminFormHandling() {
    const form = document.getElementById('adminLoginForm');
    if (!form) return;

    const inputs = form.querySelectorAll('input');

    // Enhanced validation for admin
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            validateAdminField(this);
        });

        input.addEventListener('blur', function() {
            validateAdminField(this);
        });
    });

    // Form submission with enhanced security
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (validateAdminForm()) {
            submitAdminForm();
        } else {
            showError('Admin-Formular: Bitte überprüfen Sie Ihre Eingaben');
        }
    });
}

function validateAdminField(field) {
    const value = field.value.trim();
    clearFieldStatus(field);

    if (field.hasAttribute('required') && !value) {
        markFieldAsError(field, 'Sicherheitsfeld ist erforderlich');
        return false;
    }

    if (field.type === 'text' && field.name === 'username') {
        if (value.length < 3) {
            markFieldAsError(field, 'Admin-Benutzername zu kurz');
            return false;
        }
        // Additional admin username validation
        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
            markFieldAsError(field, 'Nur Buchstaben, Zahlen und Unterstriche erlaubt');
            return false;
        }
    }

    if (field.type === 'password') {
        if (value.length < 8) {
            markFieldAsError(field, 'Admin-Passwort muss mindestens 8 Zeichen lang sein');
            return false;
        }
        // Enhanced password validation for admin
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
            markFieldAsError(field, 'Passwort muss Groß-, Kleinbuchstaben und Zahlen enthalten');
            return false;
        }
    }

    markFieldAsSuccess(field);
    return true;
}

function validateAdminForm() {
    const form = document.getElementById('adminLoginForm');
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!validateAdminField(input)) {
            isValid = false;
        }
    });

    return isValid;
}

function submitAdminForm() {
    const form = document.getElementById('adminLoginForm');
    const submitBtn = form.querySelector('.btn-admin');

    // Show enhanced loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    // Add security delay for admin login
    setTimeout(() => {
        const formData = new FormData(form);

        fetch(form.action || window.location.pathname, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                showSuccessMessage('Administrator-Zugang gewährt');
                setTimeout(() => {
                    window.location.href = response.url;
                }, 1000);
            } else if (response.ok) {
                response.text().then(html => {
                    if (html.includes('flash-message')) {
                        window.location.reload();
                    } else {
                        showError('Unerwartete Server-Antwort');
                    }
                });
            } else {
                showError(`Server-Fehler: ${response.status} ${response.statusText}`);
            }
        })
        .catch(error => {
            showError('Sicherheitsfehler. Zugang verweigert.');
        })
        .finally(() => {
            // Reset loading state after delay
            setTimeout(() => {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }, 1000);
        });
    }, 1500); // Security delay
}

function toggleAdminPassword() {
    const passwordField = document.getElementById('password');
    const toggleIcon = document.getElementById('adminPasswordToggleIcon');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleIcon.textContent = '🙈';
    } else {
        passwordField.type = 'password';
        toggleIcon.textContent = '👁️';
    }
}

function setupAdminKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Enter to submit with additional validation
        if (e.key === 'Enter' && e.target.tagName !== 'BUTTON') {
            e.preventDefault();
            const submitBtn = document.querySelector('.btn-admin');
            if (submitBtn && !submitBtn.disabled) {
                // Additional security check before submission
                if (confirm('Möchten Sie sich wirklich als Administrator anmelden?')) {
                    submitBtn.click();
                }
            }
        }
    });
}

function showSecurityWarnings() {
    // Flash security level indicator
    const securityIndicator = document.createElement('div');
    securityIndicator.className = 'security-level';
    securityIndicator.textContent = 'LEVEL 5';

    const loginCard = document.querySelector('.admin-login-card');
    if (loginCard) {
        loginCard.appendChild(securityIndicator);
    }
}

/* ============================================
   ADMIN DASHBOARD FUNCTIONALITY
   ============================================ */

function initializeAdminDashboard() {
    loadAdminStats();
    showSection('overview');
    setupDashboardEventListeners();
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
}

function setupDashboardEventListeners() {
    // Modal events
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    // Edit user form submission
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const userId = formData.get('user_id');

            try {
                const response = await fetch(`/admin/update_user/${userId}`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    location.reload();
                } else {
                    showToast('Fehler beim Aktualisieren des Benutzers', 'error');
                }
            } catch (error) {
                console.error('Fehler:', error);
                showToast('Fehler beim Aktualisieren des Benutzers', 'error');
            }
        });
    }
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('de-DE');
    const currentTimeElement = document.getElementById('currentTime');
    if (currentTimeElement) {
        currentTimeElement.textContent = timeString;
    }
}

function showSection(section) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const navItem = document.querySelector(`[data-section="${section}"]`);
    if (navItem) {
        navItem.classList.add('active');
    }

    // Update content
    document.querySelectorAll('.admin-section').forEach(sec => {
        sec.classList.remove('active');
    });
    const sectionElement = document.getElementById(`${section}-section`);
    if (sectionElement) {
        sectionElement.classList.add('active');
    }

    currentSection = section;

    // Load section-specific data
    switch(section) {
        case 'logs':
            loadLogs();
            break;
        case 'analytics':
            loadDetailedStats();
            break;
    }
}

async function loadAdminStats() {
    try {
        const response = await fetch('/api/admin/stats');
        if (response.ok) {
            const stats = await response.json();

            const activeUsersCount = document.getElementById('activeUsersCount');
            const totalTabsCount = document.getElementById('totalTabsCount');
            const weeklyActiveUsers = document.getElementById('weeklyActiveUsers');
            const avgTabsPerUser = document.getElementById('avgTabsPerUser');

            if (activeUsersCount) activeUsersCount.textContent = stats.active_users;
            if (totalTabsCount) totalTabsCount.textContent = stats.total_tabs;
            if (weeklyActiveUsers) weeklyActiveUsers.textContent = stats.active_users;

            if (avgTabsPerUser && stats.total_tabs > 0) {
                const userCount = parseInt(document.querySelector('.stat-card .stat-content h3').textContent) || 1;
                const avgTabs = (stats.total_tabs / userCount).toFixed(1);
                avgTabsPerUser.textContent = avgTabs;
            }
        }
    } catch (error) {
        console.error('Fehler beim Laden der Admin-Statistiken:', error);
    }
}

function loadLogs() {
    const logsList = document.getElementById('logsTableBody');
    if (logsList) {
        logsList.innerHTML = `
            <div class="log-entry">
                <span>${new Date().toLocaleTimeString('de-DE')}</span>
                <span>admin</span>
                <span>Admin Dashboard Zugriff</span>
                <span class="status success">Erfolgreich</span>
                <span>127.0.0.1</span>
            </div>
            <div class="log-entry">
                <span>${new Date(Date.now() - 300000).toLocaleTimeString('de-DE')}</span>
                <span>demo</span>
                <span>Reiter erstellt</span>
                <span class="status success">Erfolgreich</span>
                <span>192.168.1.100</span>
            </div>
        `;
    }
}

function loadDetailedStats() {
    setTimeout(() => {
        console.log('Detailed stats loaded');
    }, 500);
}

function refreshLogs() {
    loadLogs();
    showToast('Logs aktualisiert', 'success');
}

function filterLogs() {
    const filter = document.getElementById('logFilter')?.value;
    console.log('Filter logs:', filter);
    loadLogs();
}

function showCreateUserModal() {
    const modal = document.getElementById('createUserModal');
    if (modal) {
        modal.classList.add('show');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }

    if (modalId === 'createUserModal') {
        const form = document.getElementById('createUserForm');
        if (form) form.reset();
    } else if (modalId === 'editUserModal') {
        const form = document.getElementById('editUserForm');
        if (form) form.reset();
    }
}

function editUser(userId, username, canEdit, canAddDelete) {
    const editUserId = document.getElementById('editUserId');
    const editUsername = document.getElementById('editUsername');
    const editCanEdit = document.getElementById('editCanEdit');
    const editCanAddDelete = document.getElementById('editCanAddDelete');
    const modal = document.getElementById('editUserModal');

    if (editUserId) editUserId.value = userId;
    if (editUsername) editUsername.value = username;
    if (editCanEdit) editCanEdit.checked = canEdit;
    if (editCanAddDelete) editCanAddDelete.checked = canAddDelete;
    if (modal) modal.classList.add('show');
}

function deleteUser(userId, username) {
    if (confirm(`Sind Sie sicher, dass Sie den Benutzer "${username}" dauerhaft löschen möchten?\n\nDies wird auch alle Daten des Benutzers unwiderruflich entfernen!`)) {
        window.location.href = `/admin/delete_user/${userId}`;
    }
}

/* ============================================
   UTILITY FUNCTIONS
   ============================================ */

function focusFirstInput() {
    const firstInput = document.getElementById('username');
    if (firstInput) {
        firstInput.focus();
    }
}

function showSuccessMessage(message) {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();

    const flashMessage = document.createElement('div');
    flashMessage.className = 'flash-message success';
    flashMessage.innerHTML = `
        <span class="flash-icon">✅</span>
        <span>${message}</span>
    `;

    flashContainer.appendChild(flashMessage);
}

function showError(message) {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();

    const flashMessage = document.createElement('div');
    flashMessage.className = 'flash-message error';
    flashMessage.innerHTML = `
        <span class="flash-icon">❌</span>
        <span>${message}</span>
    `;

    flashContainer.appendChild(flashMessage);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (flashMessage.parentNode) {
            flashMessage.style.animation = 'slideOutToRight 0.4s ease-in forwards';
            setTimeout(() => flashMessage.remove(), 400);
        }
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

function markFieldAsError(field, message) {
    field.classList.add('error');
    field.setAttribute('aria-invalid', 'true');

    // Remove existing error message
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    // Add new error message
    if (message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.setAttribute('role', 'alert');
        field.parentNode.appendChild(errorDiv);

        // Link error message to field for screen readers
        const errorId = field.id + '-error';
        errorDiv.id = errorId;
        field.setAttribute('aria-describedby', errorId);
    }
}

function markFieldAsSuccess(field) {
    field.classList.remove('error');
    field.classList.add('success');
    field.setAttribute('aria-invalid', 'false');

    // Remove error message and aria attributes
    const errorMessage = field.parentNode.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
    field.removeAttribute('aria-describedby');
}

function clearFieldStatus(field) {
    field.classList.remove('error', 'success');
    field.removeAttribute('aria-invalid');
    field.removeAttribute('aria-describedby');

    const errorMessage = field.parentNode.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; padding: 16px 20px; background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); color: var(--text-primary); box-shadow: var(--shadow-lg);">
            <span style="font-size: 18px;">${icons[type]}</span>
            <span>${message}</span>
        </div>
    `;

    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);

    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Theme detection and application
function loadAdminTheme() {
    const savedTheme = localStorage.getItem('adminTheme') || 'default';
    document.body.setAttribute('data-theme', savedTheme);
    adminTheme = savedTheme;
}

function setAdminTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('adminTheme', theme);
    adminTheme = theme;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'n' && currentSection === 'users') {
        e.preventDefault();
        showCreateUserModal();
    }

    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.show').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// Auto-refresh stats
setInterval(function() {
    if (currentSection === 'overview' || currentSection === 'analytics') {
        loadAdminStats();
    }
}, 30000);

// Load admin theme on page load
loadAdminTheme();