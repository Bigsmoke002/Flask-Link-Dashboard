/* ============================================
   OPTIMIERTE USER JAVASCRIPT - PERFORMANCE EDITION
   ============================================ */

(function() {
    'use strict';

    // Globale Variablen minimiert
    let starsAnimation = null;
    let flashMessageTimeout = null;

    // ============================================
    // PERFORMANCE-OPTIMIERTE STERNE ANIMATION
    // ============================================

    class OptimizedStarField {
        constructor(canvasId = 'starsCanvas') {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) return;
            
            this.ctx = this.canvas.getContext('2d');
            this.stars = [];
            this.animationId = null;
            this.numStars = this.getOptimalStarCount();
            
            this.init();
            this.createStars();
            this.animate();
            
            // Event Listeners
            this.resizeHandler = this.handleResize.bind(this);
            window.addEventListener('resize', this.resizeHandler);
        }
        
        getOptimalStarCount() {
            // Adaptive Sterne-Anzahl basierend auf Geräteleistung
            const devicePixelRatio = window.devicePixelRatio || 1;
            const screenArea = window.innerWidth * window.innerHeight;
            
            if (screenArea < 500000) return 80;  // Mobile
            if (screenArea < 1500000) return 120; // Tablet
            return 150; // Desktop
        }
        
        init() {
            const rect = this.canvas.getBoundingClientRect();
            const devicePixelRatio = window.devicePixelRatio || 1;
            
            this.canvas.width = rect.width * devicePixelRatio;
            this.canvas.height = rect.height * devicePixelRatio;
            
            this.ctx.scale(devicePixelRatio, devicePixelRatio);
            this.canvas.style.width = rect.width + 'px';
            this.canvas.style.height = rect.height + 'px';
        }
        
        createStars() {
            this.stars = [];
            const width = this.canvas.width / (window.devicePixelRatio || 1);
            const height = this.canvas.height / (window.devicePixelRatio || 1);
            
            for(let i = 0; i < this.numStars; i++) {
                this.stars.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    size: Math.random() * 1.5 + 0.5,
                    speed: Math.random() * 0.3 + 0.1,
                    opacity: Math.random() * 0.6 + 0.2
                });
            }
        }
        
        animate() {
            if (!this.canvas) return;
            
            const width = this.canvas.width / (window.devicePixelRatio || 1);
            const height = this.canvas.height / (window.devicePixelRatio || 1);
            
            this.ctx.clearRect(0, 0, width, height);
            
            // Batch-Rendering für bessere Performance
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            
            this.stars.forEach(star => {
                star.y += star.speed;
                
                if(star.y > height) {
                    star.y = -star.size;
                    star.x = Math.random() * width;
                }
                
                this.ctx.globalAlpha = star.opacity;
                this.ctx.fillRect(star.x, star.y, star.size, star.size);
            });
            
            this.ctx.globalAlpha = 1;
            this.animationId = requestAnimationFrame(() => this.animate());
        }
        
        handleResize() {
            // Debounced resize
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.init();
                this.createStars();
            }, 250);
        }
        
        destroy() {
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
                this.animationId = null;
            }
            if (this.resizeHandler) {
                window.removeEventListener('resize', this.resizeHandler);
            }
            this.canvas = null;
            this.ctx = null;
            this.stars = null;
        }
    }

    // ============================================
    // OPTIMIERTE FORM VALIDATION
    // ============================================

    class FormValidator {
        constructor(formId) {
            this.form = document.getElementById(formId);
            if (!this.form) return;
            
            this.fields = {
                username: this.form.querySelector('#username'),
                password: this.form.querySelector('#password')
            };
            
            this.submitButton = this.form.querySelector('[type="submit"]');
            this.isSubmitting = false;
            
            this.init();
        }
        
        init() {
            // Event Listeners mit Delegation
            this.form.addEventListener('input', this.handleInput.bind(this));
            this.form.addEventListener('submit', this.handleSubmit.bind(this));
            
            // Keyboard Shortcuts
            document.addEventListener('keydown', this.handleKeyboard.bind(this));
        }
        
        handleInput(e) {
            const field = e.target;
            if (field.name && this.fields[field.name]) {
                this.validateField(field);
            }
        }
        
        validateField(field) {
            const value = field.value.trim();
            let isValid = true;
            
            // Field-spezifische Validierung
            switch(field.name) {
                case 'username':
                    isValid = value.length >= 3 && /^[a-zA-Z0-9_-]+$/.test(value);
                    break;
                case 'password':
                    isValid = value.length >= 6;
                    break;
            }
            
            // Visual Feedback
            field.classList.toggle('error', !isValid);
            return isValid;
        }
        
        validateAll() {
            let allValid = true;
            
            Object.values(this.fields).forEach(field => {
                if (field && !this.validateField(field)) {
                    allValid = false;
                }
            });
            
            return allValid;
        }
        
        handleSubmit(e) {
            if (this.isSubmitting) {
                e.preventDefault();
                return;
            }
            
            if (!this.validateAll()) {
                e.preventDefault();
                this.showError('Bitte überprüfen Sie Ihre Eingaben');
                return;
            }
            
            this.startLoadingState();
            // Form wird normal übertragen
        }
        
        startLoadingState() {
            if (!this.submitButton) return;
            
            this.isSubmitting = true;
            this.submitButton.disabled = true;
            
            const content = this.submitButton.querySelector('.button-content');
            if (content) {
                content.innerHTML = `
                    <span class="loading-spinner"></span>
                    <span>Wird verarbeitet...</span>
                `;
            }
        }
        
        showError(message) {
            // Bestehende Fehler entfernen
            const existingError = this.form.querySelector('.error-message');
            if (existingError) {
                existingError.remove();
            }
            
            // Neue Fehlermeldung
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            errorDiv.style.cssText = `
                background: rgba(237, 66, 69, 0.1);
                border: 1px solid rgba(237, 66, 69, 0.3);
                color: #ef4444;
                padding: 12px 16px;
                border-radius: 8px;
                margin-top: 16px;
                font-size: 14px;
                text-align: center;
                animation: slideUp 0.3s ease-out;
            `;
            
            this.form.appendChild(errorDiv);
            
            // Auto-Remove nach 5 Sekunden
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.style.opacity = '0';
                    errorDiv.style.transform = 'translateY(-10px)';
                    setTimeout(() => errorDiv.remove(), 300);
                }
            }, 5000);
        }
        
        handleKeyboard(e) {
            // Enter für Submit (wenn Felder ausgefüllt)
            if (e.key === 'Enter' && !this.isSubmitting) {
                const activeElement = document.activeElement;
                if (Object.values(this.fields).includes(activeElement)) {
                    if (this.validateAll()) {
                        this.form.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
                }
            }
        }
    }

    // ============================================
    // OPTIMIERTE FLASH MESSAGES
    // ============================================

    class FlashMessageManager {
        constructor() {
            this.container = document.querySelector('.flash-messages');
            if (this.container) {
                this.init();
            }
        }
        
        init() {
            const messages = this.container.querySelectorAll('.flash-message');
            messages.forEach(message => this.setupMessage(message));
        }
        
        setupMessage(message) {
            // Click to dismiss
            message.addEventListener('click', () => this.dismissMessage(message));
            
            // Auto-dismiss nach 5 Sekunden
            setTimeout(() => this.dismissMessage(message), 5000);
        }
        
        dismissMessage(message) {
            if (message.parentNode) {
                message.style.opacity = '0';
                message.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 300);
            }
        }
        
        addMessage(text, type = 'info') {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'flash-messages';
                document.body.appendChild(this.container);
            }
            
            const message = document.createElement('div');
            message.className = `flash-message ${type}`;
            message.innerHTML = `
                <span class="flash-icon">${this.getIcon(type)}</span>
                <span>${text}</span>
            `;
            
            this.container.appendChild(message);
            this.setupMessage(message);
            
            return message;
        }
        
        getIcon(type) {
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            return icons[type] || icons.info;
        }
    }

    // ============================================
    // PASSWORT SICHTBARKEIT
    // ============================================

    function initPasswordToggle() {
        const toggleButtons = document.querySelectorAll('.visibility-toggle');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const wrapper = this.closest('.input-wrapper');
                const passwordField = wrapper.querySelector('input[type="password"], input[type="text"]');
                const icon = this.querySelector('#passwordToggleIcon') || this.querySelector('span');
                
                if (passwordField.type === 'password') {
                    passwordField.type = 'text';
                    if (icon) icon.textContent = '🙈';
                } else {
                    passwordField.type = 'password';
                    if (icon) icon.textContent = '👁️';
                }
            });
        });
    }

    // ============================================
    // THEME SYSTEM (falls vorhanden)
    // ============================================

    class ThemeManager {
        constructor() {
            this.currentTheme = localStorage.getItem('theme') || 'default';
            this.applyTheme(this.currentTheme);
        }
        
        applyTheme(theme) {
            document.body.setAttribute('data-theme', theme);
            this.currentTheme = theme;
            localStorage.setItem('theme', theme);
        }
        
        toggleTheme() {
            const themes = ['default', 'purple', 'green', 'red', 'blue', 'pink'];
            const currentIndex = themes.indexOf(this.currentTheme);
            const nextIndex = (currentIndex + 1) % themes.length;
            this.applyTheme(themes[nextIndex]);
        }
    }

    // ============================================
    // PERFORMANCE MONITORING
    // ============================================

    class PerformanceMonitor {
        constructor() {
            this.startTime = performance.now();
            this.init();
        }
        
        init() {
            // Page Load Performance
            window.addEventListener('load', () => {
                const loadTime = performance.now() - this.startTime;
                console.log(`🚀 Page loaded in ${loadTime.toFixed(2)}ms`);
            });
            
            // Memory Usage (falls verfügbar)
            if ('memory' in performance) {
                setInterval(() => {
                    const memory = performance.memory;
                    if (memory.usedJSHeapSize > 50000000) { // 50MB
                        console.warn('⚠️ High memory usage detected');
                    }
                }, 30000);
            }
        }
    }

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================

    const utils = {
        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Throttle function
        throttle(func, limit) {
            let lastFunc;
            let lastRan;
            return function(...args) {
                if (!lastRan) {
                    func(...args);
                    lastRan = Date.now();
                } else {
                    clearTimeout(lastFunc);
                    lastFunc = setTimeout(() => {
                        if ((Date.now() - lastRan) >= limit) {
                            func(...args);
                            lastRan = Date.now();
                        }
                    }, limit - (Date.now() - lastRan));
                }
            };
        },
        
        // Check if element is in viewport
        isInViewport(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        }
    };

    // ============================================
    // GLOBAL FUNCTIONS (für Templates)
    // ============================================

    window.togglePassword = function() {
        const passwordField = document.getElementById('password');
        const toggleIcon = document.getElementById('passwordToggleIcon');
        
        if (passwordField && toggleIcon) {
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                toggleIcon.textContent = '🙈';
            } else {
                passwordField.type = 'password';
                toggleIcon.textContent = '👁️';
            }
        }
    };

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {
        // Core Features
        const flashManager = new FlashMessageManager();
        const performanceMonitor = new PerformanceMonitor();
        
        // Conditional Features
        if (document.getElementById('starsCanvas')) {
            starsAnimation = new OptimizedStarField();
        }
        
        if (document.querySelector('form')) {
            const formValidator = new FormValidator(document.querySelector('form').id);
        }
        
        // Password Toggle
        initPasswordToggle();
        
        // Theme System (falls Theme-Buttons vorhanden)
        if (document.querySelector('[data-theme-toggle]')) {
            const themeManager = new ThemeManager();
            document.addEventListener('click', (e) => {
                if (e.target.matches('[data-theme-toggle]')) {
                    themeManager.toggleTheme();
                }
            });
        }
        
        // Focus Management
        const firstInput = document.querySelector('input[type="text"], input[type="email"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        console.log('✅ User JavaScript initialized');
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================

    // DOM Ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Page Unload Cleanup
    window.addEventListener('beforeunload', () => {
        if (starsAnimation) {
            starsAnimation.destroy();
        }
        if (flashMessageTimeout) {
            clearTimeout(flashMessageTimeout);
        }
    });

    // Error Handling
    window.addEventListener('error', (e) => {
        console.error('❌ JavaScript Error:', e.error);
        // Optional: Send to error reporting service
    });

    window.addEventListener('unhandledrejection', (e) => {
        console.error('❌ Unhandled Promise Rejection:', e.reason);
        // Optional: Send to error reporting service
    });

    // ============================================
    // EXPORTS (für Module)
    // ============================================

    window.DashboardJS = {
        utils,
        FlashMessageManager,
        OptimizedStarField,
        FormValidator,
        ThemeManager
    };

})();