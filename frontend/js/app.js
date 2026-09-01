/**
 * Main Application Module
 * Initializes the app, the sidebar/topbar shell and manages overall state.
 */

function ensureToastContainer() {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }
  return container;
}

window.showToast = function(message, type = 'info') {
  if (typeof document === 'undefined') return;

  const container = ensureToastContainer();
  const visibleToasts = container.querySelectorAll('.toast');
  if (visibleToasts.length >= 3) {
    visibleToasts[0].remove();
  }

  const toast = document.createElement('div');
  const iconMap = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
  };
  const safeType = ['success', 'error', 'info'].includes(type) ? type : 'info';

  toast.className = `toast toast--${safeType}`;
  toast.innerHTML = `
    <span class="toast__icon" aria-hidden="true">${iconMap[safeType]}</span>
    <div class="toast__body">${String(message || '')}</div>
    <button type="button" class="toast__close" aria-label="Cerrar aviso">×</button>
  `;

  const removeToast = () => {
    if (!toast.isConnected) return;
    toast.classList.add('toast--closing');
    window.setTimeout(() => toast.remove(), 220);
  };

  const timerId = window.setTimeout(removeToast, 3000);
  toast.querySelector('.toast__close').addEventListener('click', () => {
    window.clearTimeout(timerId);
    removeToast();
  });

  container.appendChild(toast);
  window.requestAnimationFrame(() => {
    toast.classList.add('toast--visible');
  });
};

window.showConfirmDialog = function(message, options = {}) {
  return new Promise((resolve) => {
    const modal = document.createElement('div');
    modal.className = 'modal confirm-modal';
    modal.style.display = 'flex';

    const title = options.title || 'Confirmación';
    const confirmText = options.confirmText || 'Confirmar';
    const cancelText = options.cancelText || 'Cancelar';

    modal.innerHTML = `
      <div class="modal__overlay"></div>
      <div class="modal__content confirm-modal__content">
        <h3 style="margin-bottom: var(--space-3);">${title}</h3>
        <p style="margin-bottom: var(--space-5); color: var(--text-muted);">${message}</p>
        <div style="display: flex; justify-content: flex-end; gap: var(--space-3); flex-wrap: wrap;">
          <button type="button" class="btn btn--outline" data-confirm-action="cancel">${cancelText}</button>
          <button type="button" class="btn btn--primary" data-confirm-action="confirm">${confirmText}</button>
        </div>
      </div>
    `;

    const cleanup = (result) => {
      modal.remove();
      resolve(result);
    };

    modal.querySelector('.modal__overlay').addEventListener('click', () => cleanup(false));
    modal.querySelector('[data-confirm-action="cancel"]').addEventListener('click', () => cleanup(false));
    modal.querySelector('[data-confirm-action="confirm"]').addEventListener('click', () => cleanup(true));

    document.body.appendChild(modal);
  });
};

class Application {
  constructor() {
    this.initialized = false;
    this.initializationPromise = this.initialize();
  }

  /**
   * Initialize the application
   */
  async initialize() {
    if (this.initialized) return;

    try {
      console.log('[App] Initializing...');

      // Setup UI listeners
      this.setupUIListeners();

      // Setup authentication listeners
      this.setupAuthListeners();

      // Setup navigation (sidebar links)
      this.setupNavigation();

      // Setup the sidebar shell (collapse, mobile toggle, section fold)
      this.setupShell();

      // Check API connectivity
      await this.checkAPIConnectivity();

      // Update UI based on current auth state
      this.updateUIForAuthState();

      // Initialize home page
      router.navigate('home');
      this.updateNavLinks();

      this.initialized = true;
      console.log('[App] Initialized successfully');

      return true;
    } catch (error) {
      console.error('[App] Initialization error:', error);
      showToast('Error inicializando la aplicación', 'error');
      return false;
    }
  }

  /**
   * Setup UI listeners
   */
  setupUIListeners() {
    // Close alerts
    document.getElementById('error-close')?.addEventListener('click', () => {
      UI.hideError();
    });

    document.getElementById('success-close')?.addEventListener('click', () => {
      UI.hideSuccess();
    });

    // Modal close
    document.getElementById('auth-modal-close')?.addEventListener('click', () => {
      router.closeAuthModal();
    });

    document.getElementById('modal-overlay')?.addEventListener('click', () => {
      router.closeAuthModal();
    });

    // Auth (login) button — only relevant when NOT authenticated
    document.getElementById('auth-button')?.addEventListener('click', () => {
      if (!authSystem.isAuthenticated()) {
        router.showAuthModal();
      }
    });

    // Logout button
    document.getElementById('logout-button')?.addEventListener('click', () => {
      showConfirmDialog('¿Cerrar sesión?', {
        title: 'Cerrar sesión',
        confirmText: 'Cerrar sesión',
        cancelText: 'Cancelar',
      }).then((confirmed) => {
        if (!confirmed) return;

        authSystem.logout();
        showToast('Sesión cerrada', 'info');
        this.updateUIForAuthState();
        setTimeout(() => {
          router.navigate('home');
          this.updateNavLinks();
        }, 800);
      });
    });
  }

  /**
   * Setup authentication listeners
   */
  setupAuthListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleLogin();
      });
    }

    // Signup form
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
      signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleSignup();
      });
    }

    // Tab switching
    document.getElementById('switch-to-signup')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthTab('signup');
    });

    document.getElementById('switch-to-login')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthTab('login');
    });

    // Listen for auth changes from other tabs
    window.addEventListener('authChange', () => {
      this.updateUIForAuthState();
    });
  }

  /**
   * Handle login
   */
  async handleLogin() {
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
      showToast('Correo y contraseña son requeridos', 'error');
      return;
    }

    const result = await authSystem.login(email, password);

    if (!result.success) {
      showToast(result.error, 'error');
      return;
    }

    showToast(`¡Bienvenido, ${result.user.name}!`, 'success');
    router.closeAuthModal();
    UI.clearForm('login-form');

    setTimeout(() => {
      this.updateUIForAuthState();
      router.navigate('home');
      this.updateNavLinks();
    }, 1200);
  }

  /**
   * Handle signup
   */
  async handleSignup() {
    const nameInput = document.getElementById('signup-name');
    const emailInput = document.getElementById('signup-email');
    const passwordInput = document.getElementById('signup-password');

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!name || !email || !password) {
      showToast('Todos los campos son requeridos', 'error');
      return;
    }

    if (!Validation.isValidEmail(email)) {
      showToast('El correo no es válido', 'error');
      return;
    }

    if (!Validation.isValidPassword(password)) {
      showToast('La contraseña debe tener entre 8 caracteres y 72 bytes, una letra y un carácter especial', 'error');
      return;
    }

    // Signup as candidate (always)
    const result = await authSystem.signup(name, email, password);

    if (!result.success) {
      showToast(result.error, 'error');
      return;
    }

    showToast('¡Cuenta creada exitosamente!', 'success');
    router.closeAuthModal();
    UI.clearForm('signup-form');

    setTimeout(() => {
      this.updateUIForAuthState();
      router.navigate('home');
      this.updateNavLinks();
    }, 1200);
  }

  /**
   * Switch auth tab
   */
  switchAuthTab(tab) {
    document.getElementById('login-tab').classList.remove('auth-modal__tab--active');
    document.getElementById('signup-tab').classList.remove('auth-modal__tab--active');
    document.getElementById(`${tab}-tab`).classList.add('auth-modal__tab--active');
  }

  /**
   * Setup navigation (sidebar links with data-page)
   */
  setupNavigation() {
    document.querySelectorAll('.sidebar__link[data-page]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        const navigated = router.navigate(page);
        if (navigated !== false) {
          this.updateNavLinks();
          this.closeMobileSidebar();
        }
      });
    });
  }

  /**
   * Setup the app shell: collapse button, mobile toggle, section fold.
   */
  setupShell() {
    const shell = document.getElementById('app-shell');

    // Mobile hamburger toggle
    document.getElementById('topbar-menu-btn')?.addEventListener('click', () => {
      shell.classList.toggle('sidebar-open');
    });

    // Mobile backdrop closes the sidebar
    document.getElementById('sidebar-backdrop')?.addEventListener('click', () => {
      this.closeMobileSidebar();
    });

    // Collapsible "Plataforma" section
    document.getElementById('sidebar-section-toggle')?.addEventListener('click', () => {
      document.getElementById('sidebar-section-platform')?.classList.toggle('collapsed');
    });
  }

  closeMobileSidebar() {
    document.getElementById('app-shell')?.classList.remove('sidebar-open');
  }

  /**
   * Update UI based on authentication state.
   * Controls sidebar visibility, topbar user info and role-based nav items.
   */
  updateUIForAuthState() {
    const isAuthenticated = authSystem.isAuthenticated();
    const user = authSystem.getCurrentUser();

    const shell = document.getElementById('app-shell');
    const authBtn = document.getElementById('auth-button');
    const userMenu = document.getElementById('user-menu');
    const userAvatar = document.getElementById('user-avatar');
    const logoutBtn = document.getElementById('logout-button');

    if (isAuthenticated && user) {
      // Show sidebar shell
      shell?.classList.remove('no-sidebar');
      shell?.classList.toggle('sidebar-collapsed', ['admin', 'hr'].includes(user.role));

      // Ensure the "Plataforma" section is expanded so its nav items are visible
      document.getElementById('sidebar-section-platform')?.classList.remove('collapsed');

      // Topbar: hide login button, show user info + logout
      if (authBtn) authBtn.style.display = 'none';
      if (userMenu) userMenu.style.display = 'flex';
      if (userAvatar) {
        userAvatar.style.display = 'flex';
        userAvatar.textContent = (user.name || user.email || '?').charAt(0).toUpperCase();
      }
      if (logoutBtn) logoutBtn.style.display = 'inline-flex';

      document.getElementById('user-info').textContent = user.email || user.name || '';
      const roleEl = document.getElementById('user-role');
      if (roleEl) roleEl.textContent = this.roleLabel(user.role);

      // Role-based visibility of sidebar items
      this.applyRoleVisibility(user.role);
    } else {
      // Hide sidebar shell (full-width content + login)
      shell?.classList.add('no-sidebar');
      shell?.classList.remove('sidebar-collapsed');
      this.closeMobileSidebar();

      if (authBtn) authBtn.style.display = 'inline-flex';
      if (userMenu) userMenu.style.display = 'none';
      if (userAvatar) userAvatar.style.display = 'none';
      if (logoutBtn) logoutBtn.style.display = 'none';

      this.applyRoleVisibility(null);
    }
  }

  /**
   * Show/hide sidebar items based on the user's role.
   * data-nav-role: 'all' | 'candidate' | 'hr' | 'admin'
   *   - all   → everyone authenticated
   *   - hr    → hr and admin
   *   - admin → admin only
   */
  applyRoleVisibility(role) {
    document.querySelectorAll('.sidebar__link[data-nav-role]').forEach(link => {
      const required = link.dataset.navRole;
      let visible = false;

      if (role) {
        if (required === 'all') visible = true;
        else if (required === 'candidate') visible = role === 'candidate';
        else if (required === 'hr') visible = role === 'hr' || role === 'admin';
        else if (required === 'admin') visible = role === 'admin';
      }

      // Set display on both the <a> (which may carry an inline display:none from the HTML)
      // and its <li> parent so no empty space remains when hidden.
      link.style.display = visible ? '' : 'none';
      link.parentElement.style.display = visible ? '' : 'none';
    });
  }

  roleLabel(role) {
    const labels = { candidate: 'Candidato', hr: 'Recursos Humanos', admin: 'Administrador' };
    return labels[role] || role || '';
  }

  /**
   * Update nav links active state and topbar title.
   */
  updateNavLinks() {
    document.querySelectorAll('.sidebar__link[data-page]').forEach(link => {
      link.classList.remove('sidebar__link--active');
    });

    const currentPage = router.getCurrentPage();
    const activeLink = document.querySelector(`.sidebar__link[data-page="${currentPage}"]`);
    if (activeLink) {
      activeLink.classList.add('sidebar__link--active');
    }

    // Sync topbar title with the current route
    const route = router.getRoute(currentPage);
    const titleEl = document.getElementById('topbar-title');
    if (titleEl && route?.navTitle) {
      titleEl.textContent = route.navTitle;
    }
  }

  /**
   * Check API connectivity
   */
  async checkAPIConnectivity() {
    try {
      const result = await apiClient.healthCheck();
      if (!result.message) {
        console.warn('[App] Backend health check failed');
      } else {
        console.log('[App] Backend is ready');
      }
    } catch (error) {
      console.warn('[App] Backend not available, using cached data', error.message);
    }
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.app = new Application();
  });
} else {
  window.app = new Application();
}
