/**
 * Utilities Module
 * Helper functions for common operations
 */

const UI = {
  /**
   * Show loading state
   */
  showLoading() {
    document.getElementById('loading-state').style.display = 'flex';
  },

  /**
   * Hide loading state
   */
  hideLoading() {
    document.getElementById('loading-state').style.display = 'none';
  },

  /**
   * Show success message
   */
  showSuccess(message) {
    const el = document.getElementById('success-state');
    const msgEl = document.getElementById('success-message');
    msgEl.textContent = message;
    el.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
      this.hideSuccess();
    }, 5000);
  },

  /**
   * Hide success message
   */
  hideSuccess() {
    document.getElementById('success-state').style.display = 'none';
  },

  /**
   * Show error message
   */
  showError(message) {
    const el = document.getElementById('error-state');
    const msgEl = document.getElementById('error-message');
    msgEl.textContent = message;
    el.style.display = 'block';

    // Auto-hide after 7 seconds
    setTimeout(() => {
      this.hideError();
    }, 7000);
  },

  /**
   * Hide error message
   */
  hideError() {
    document.getElementById('error-state').style.display = 'none';
  },

  /**
   * Show/hide page
   */
  showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
      page.classList.remove('page--active');
    });

    // Show target page
    const page = document.getElementById(pageId);
    if (page) {
      page.classList.add('page--active');
    }
  },

  /**
   * Clear form
   */
  clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
      form.reset();
    }
  },
};

/**
 * Format utilities
 */
const Format = {
  /**
   * Format date
   */
  date(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  },

  /**
   * Format datetime
   */
  dateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  /**
   * Format file size
   */
  fileSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
  },

  /**
   * Truncate text
   */
  truncate(text, length = 100) {
    if (!text) return '';
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
  },
};

/**
 * Validation utilities
 */
const Validation = {
  /**
   * Validate email
   */
  isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },

  /**
   * Validate password
   */
  isValidPassword(password) {
    return typeof password === 'string'
      && Array.from(password).length >= 8
      && /\p{L}/u.test(password)
      && /[\p{P}\p{S}]/u.test(password);
  },

  /**
   * Validate file type
   */
  isValidPDF(file) {
    return file && file.type === 'application/pdf';
  },

  /**
   * Validate file size (max 5MB)
   */
  isValidFileSize(file, maxMB = 5) {
    return file && file.size <= maxMB * 1024 * 1024;
  },
};

/**
 * Storage utilities
 */
const Storage = {
  /**
   * Save job cache
   */
  saveJobCache(jobs) {
    localStorage.setItem('job_cache', JSON.stringify({
      jobs,
      timestamp: Date.now(),
    }));
  },

  /**
   * Get job cache
   */
  getJobCache(maxAgeMs = 5 * 60 * 1000) {
    const cached = localStorage.getItem('job_cache');
    if (!cached) return null;

    const data = JSON.parse(cached);
    if (Date.now() - data.timestamp > maxAgeMs) {
      localStorage.removeItem('job_cache');
      return null;
    }

    return data.jobs;
  },

  /**
   * Save application cache
   */
  saveApplicationCache(applications) {
    localStorage.setItem('app_cache', JSON.stringify({
      applications,
      timestamp: Date.now(),
    }));
  },

  /**
   * Get application cache
   */
  getApplicationCache(maxAgeMs = 5 * 60 * 1000) {
    const cached = localStorage.getItem('app_cache');
    if (!cached) return null;

    const data = JSON.parse(cached);
    if (Date.now() - data.timestamp > maxAgeMs) {
      localStorage.removeItem('app_cache');
      return null;
    }

    return data.applications;
  },

  /**
   * Clear all caches
   */
  clearAllCaches() {
    localStorage.removeItem('job_cache');
    localStorage.removeItem('app_cache');
  },
};

/**
 * DOM utilities
 */
const DOM = {
  /**
   * Get element safely
   */
  get(id) {
    return document.getElementById(id);
  },

  /**
   * Get elements
   */
  getAll(selector) {
    return document.querySelectorAll(selector);
  },

  /**
   * Set text content
   */
  setText(id, text) {
    const el = this.get(id);
    if (el) el.textContent = text;
  },

  /**
   * Set HTML content
   */
  setHTML(id, html) {
    const el = this.get(id);
    if (el) el.innerHTML = html;
  },

  /**
   * Add event listener
   */
  on(id, event, handler) {
    const el = this.get(id);
    if (el) el.addEventListener(event, handler);
  },

  /**
   * Show element
   */
  show(id) {
    const el = this.get(id);
    if (el) el.style.display = '';
  },

  /**
   * Hide element
   */
  hide(id) {
    const el = this.get(id);
    if (el) el.style.display = 'none';
  },
};

// Export all utilities
window.UI = UI;
window.Format = Format;
window.Validation = Validation;
window.Storage = Storage;
window.DOM = DOM;
