/* News Aggregator - JavaScript Components */

class NewsAggregator {
    constructor() {
        this.init();
    }

    init() {
        this.initTooltips();
        this.initNavigation();
        this.initNotifications();
        this.initLoadingStates();
    }

    // Initialize Bootstrap tooltips
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Navigation helpers
    initNavigation() {
        // Mobile menu toggle
        const navToggle = document.querySelector('.navbar-toggler');
        if (navToggle) {
            navToggle.addEventListener('click', this.toggleMobileMenu);
        }

        // Sidebar navigation
        this.initSidebarNavigation();
    }

    initSidebarNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Notification system
    initNotifications() {
        this.notificationContainer = this.createNotificationContainer();
    }

    createNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.notificationContainer.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 150);
            }
        }, duration);
    }

    // Loading states
    initLoadingStates() {
        this.originalButtonTexts = new Map();
    }

    showLoading(element, text = 'Laden...') {
        if (element.tagName === 'BUTTON') {
            if (!this.originalButtonTexts.has(element)) {
                this.originalButtonTexts.set(element, element.innerHTML);
            }
            element.innerHTML = `<span class="spinner"></span>${text}`;
            element.disabled = true;
        } else {
            element.classList.add('loading');
        }
    }

    hideLoading(element) {
        if (element.tagName === 'BUTTON') {
            if (this.originalButtonTexts.has(element)) {
                element.innerHTML = this.originalButtonTexts.get(element);
                this.originalButtonTexts.delete(element);
            }
            element.disabled = false;
        } else {
            element.classList.remove('loading');
        }
    }

    // API helpers
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffHours < 1) {
            return 'Gerade eben';
        } else if (diffHours < 24) {
            return `vor ${diffHours} Stunde${diffHours !== 1 ? 'n' : ''}`;
        } else if (diffDays < 7) {
            return `vor ${diffDays} Tag${diffDays !== 1 ? 'en' : ''}`;
        } else {
            return date.toLocaleDateString('de-DE');
        }
    }

    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    // Mobile helpers
    isMobile() {
        return window.innerWidth <= 768;
    }

    // Touch event helpers
    initTouchEvents() {
        let startY = 0;
        let startX = 0;

        document.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
        });

        document.addEventListener('touchmove', (e) => {
            if (!startY || !startX) return;

            const currentY = e.touches[0].clientY;
            const currentX = e.touches[0].clientX;
            const diffY = startY - currentY;
            const diffX = startX - currentX;

            // Detect swipe gestures
            if (Math.abs(diffY) > Math.abs(diffX)) {
                if (diffY > 50) {
                    // Swipe up
                    this.onSwipeUp && this.onSwipeUp();
                } else if (diffY < -50) {
                    // Swipe down
                    this.onSwipeDown && this.onSwipeDown();
                }
            } else {
                if (diffX > 50) {
                    // Swipe left
                    this.onSwipeLeft && this.onSwipeLeft();
                } else if (diffX < -50) {
                    // Swipe right
                    this.onSwipeRight && this.onSwipeRight();
                }
            }

            startY = 0;
            startX = 0;
        });
    }
}

// Article Management
class ArticleManager {
    constructor(app) {
        this.app = app;
    }

    async rateArticle(articleId, rating) {
        try {
            const response = await this.app.apiCall(`/articles/rate/${articleId}`, {
                method: 'POST',
                body: JSON.stringify({ rating: rating })
            });

            if (response.success) {
                this.app.showNotification(`Artikel als ${rating} bewertet`, 'success');
                return true;
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            this.app.showNotification(`Fehler beim Bewerten: ${error.message}`, 'danger');
            return false;
        }
    }

    filterArticles(filter) {
        const articles = document.querySelectorAll('.article-card');
        const filterButtons = document.querySelectorAll('.filter-btn');

        // Update active filter button
        filterButtons.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-filter="${filter}"]`)?.classList.add('active');

        // Filter articles
        articles.forEach(article => {
            let show = false;
            
            switch(filter) {
                case 'all':
                    show = true;
                    break;
                case 'telegram':
                    show = article.dataset.source === 'telegram';
                    break;
                case 'unrated':
                    show = article.dataset.rating === 'unrated';
                    break;
                case 'high':
                    show = article.dataset.rating === 'high';
                    break;
                case 'twitter':
                    show = article.dataset.twitter === 'yes';
                    break;
            }
            
            article.style.display = show ? 'block' : 'none';
        });
    }
}

// Telegram Management
class TelegramManager {
    constructor(app) {
        this.app = app;
    }

    async addChannel(channelData) {
        try {
            const response = await this.app.apiCall('/telegram/add-channel', {
                method: 'POST',
                body: JSON.stringify(channelData)
            });

            if (response.success) {
                this.app.showNotification(`Channel @${channelData.channel_username} hinzugefügt`, 'success');
                return true;
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            this.app.showNotification(`Fehler beim Hinzufügen: ${error.message}`, 'danger');
            return false;
        }
    }

    async removeChannel(sourceId) {
        try {
            const response = await this.app.apiCall(`/telegram/remove-channel/${sourceId}`, {
                method: 'DELETE'
            });

            if (response.success) {
                this.app.showNotification('Channel entfernt', 'success');
                return true;
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            this.app.showNotification(`Fehler beim Entfernen: ${error.message}`, 'danger');
            return false;
        }
    }

    async testBot() {
        try {
            const response = await this.app.apiCall('/telegram/test-bot');

            if (response.success) {
                this.app.showNotification(`Bot-Verbindung OK: ${response.bot_info}`, 'success');
                return true;
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            this.app.showNotification(`Bot-Test fehlgeschlagen: ${error.message}`, 'danger');
            return false;
        }
    }

    async manualSync() {
        try {
            const response = await this.app.apiCall('/telegram/manual-sync', {
                method: 'POST'
            });

            if (response.success) {
                this.app.showNotification(`Sync abgeschlossen: ${response.new_articles} neue Artikel`, 'success');
                return response.new_articles;
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            this.app.showNotification(`Sync fehlgeschlagen: ${error.message}`, 'danger');
            return 0;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.newsApp = new NewsAggregator();
    window.articleManager = new ArticleManager(window.newsApp);
    window.telegramManager = new TelegramManager(window.newsApp);
    
    // Initialize touch events for mobile
    if (window.newsApp.isMobile()) {
        window.newsApp.initTouchEvents();
    }
});
