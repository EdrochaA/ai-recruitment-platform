/**
 * Theme Toggle System
 * Handles light/dark mode switching with localStorage persistence
 */

class ThemeToggle {
  constructor() {
    this.STORAGE_KEY = 'ai_recruitment_theme';
    this.DARK_CLASS = 'dark-mode';
    this.init();
  }

  init() {
    // Load saved preference or detect system preference
    const savedTheme = localStorage.getItem(this.STORAGE_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme ? savedTheme === 'dark' : prefersDark;

    if (isDark) {
      this.enableDarkMode();
    } else {
      this.disableDarkMode();
    }

    // Setup toggle button listener
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggle());
    }
  }

  toggle() {
    const isDark = document.body.classList.contains(this.DARK_CLASS);
    if (isDark) {
      this.disableDarkMode();
    } else {
      this.enableDarkMode();
    }
  }

  enableDarkMode() {
    document.body.classList.add(this.DARK_CLASS);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.textContent = '☀️';
      themeToggle.title = 'Cambiar a modo claro';
    }
    localStorage.setItem(this.STORAGE_KEY, 'dark');
  }

  disableDarkMode() {
    document.body.classList.remove(this.DARK_CLASS);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.textContent = '🌙';
      themeToggle.title = 'Cambiar a modo oscuro';
    }
    localStorage.setItem(this.STORAGE_KEY, 'light');
  }
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeToggle = new ThemeToggle();
  });
} else {
  window.themeToggle = new ThemeToggle();
}
