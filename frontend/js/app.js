/**
 * Main Application Module
 * Initializes the app and manages overall state
 */

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

      // Setup navigation
      this.setupNavigation();

      // Check API connectivity
      await this.checkAPIConnectivity();

      // Update UI based on current auth state
      this.updateUIForAuthState();

      // Initialize home page
      router.navigate('home');

      this.initialized = true;
      console.log('[App] Initialized successfully');

      return true;
    } catch (error) {
      console.error('[App] Initialization error:', error);
      UI.showError('Error inicializando la aplicación');
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

    // Auth button
    document.getElementById('auth-button')?.addEventListener('click', () => {
      if (authSystem.isAuthenticated()) {
        // Show user menu
        this.toggleUserMenu();
      } else {
        // Show auth modal
        router.showAuthModal();
      }
    });

    // Logout button
    document.getElementById('logout-button')?.addEventListener('click', () => {
      authSystem.logout();
      UI.showSuccess('Sesión cerrada');
      setTimeout(() => {
        router.navigate('home');
      }, 1000);
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
      UI.showError('Correo y contraseña son requeridos');
      return;
    }

    const result = await authSystem.login(email, password);

    if (!result.success) {
      UI.showError(result.error);
      return;
    }

    UI.showSuccess(`¡Bienvenido, ${result.user.name}!`);
    router.closeAuthModal();
    UI.clearForm('login-form');

    setTimeout(() => {
      this.updateUIForAuthState();
      // Navigate based on role
      const user = authSystem.getCurrentUser();
      if (user.role === 'hr') {
        router.navigate('hr-dashboard');
      } else if (user.role === 'admin') {
        router.navigate('admin-dashboard');
      } else {
        router.navigate('home');
      }
    }, 1500);
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
      UI.showError('Todos los campos son requeridos');
      return;
    }

    if (!Validation.isValidEmail(email)) {
      UI.showError('El correo no es válido');
      return;
    }

    if (!Validation.isValidPassword(password)) {
      UI.showError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    // Signup as candidate (always)
    const result = await authSystem.signup(name, email, password);

    if (!result.success) {
      UI.showError(result.error);
      return;
    }

    UI.showSuccess('¡Cuenta creada exitosamente!');
    router.closeAuthModal();
    UI.clearForm('signup-form');

    setTimeout(() => {
      this.updateUIForAuthState();
      router.navigate('home');
    }, 1500);
  }

  /**
   * Switch auth tab
   */
  switchAuthTab(tab) {
    // Hide all tabs
    document.getElementById('login-tab').classList.remove('auth-modal__tab--active');
    document.getElementById('signup-tab').classList.remove('auth-modal__tab--active');

    // Show target tab
    document.getElementById(`${tab}-tab`).classList.add('auth-modal__tab--active');
  }

  /**
   * Toggle user menu
   */
  toggleUserMenu() {
    const userMenu = document.getElementById('user-menu');
    const authBtn = document.getElementById('auth-button');

    if (userMenu.style.display === 'none' || !userMenu.style.display) {
      userMenu.style.display = 'block';
    } else {
      userMenu.style.display = 'none';
    }
  }

  /**
   * Setup navigation
   */
  setupNavigation() {
    // Navigation links
    document.querySelectorAll('[data-page]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.dataset.page;
        router.navigate(page);
        this.updateNavLinks();
      });
    });

    // Dashboard links
    document.getElementById('nav-dashboard-link')?.addEventListener('click', (e) => {
      e.preventDefault();
      const user = authSystem.getCurrentUser();
      if (user.role === 'hr') {
        router.navigate('hr-dashboard');
      } else if (user.role === 'admin') {
        router.navigate('admin-dashboard');
      }
    });

    document.getElementById('dashboard-link')?.addEventListener('click', (e) => {
      e.preventDefault();
      const user = authSystem.getCurrentUser();
      if (user.role === 'hr') {
        router.navigate('hr-dashboard');
      } else if (user.role === 'admin') {
        router.navigate('admin-dashboard');
      }
    });
  }

  /**
   * Update UI based on authentication state
   */
  updateUIForAuthState() {
    const isAuthenticated = authSystem.isAuthenticated();
    const user = authSystem.getCurrentUser();

    const authBtn = document.getElementById('auth-button');
    const userMenu = document.getElementById('user-menu');
    const dashboardLink = document.getElementById('nav-dashboard-link');
    const dashboardMenuLink = document.getElementById('dashboard-link');

    if (isAuthenticated) {
      // Show user menu
      authBtn.textContent = user.name;
      document.getElementById('user-info').textContent = `${user.name} (${user.role})`;

      // Show dashboard link if HR or Admin
      if (user.role === 'hr' || user.role === 'admin') {
        dashboardLink.style.display = 'inline-block';
        dashboardMenuLink.style.display = 'block';
      } else {
        dashboardLink.style.display = 'none';
        dashboardMenuLink.style.display = 'none';
      }

      // Close user menu
      if (userMenu) userMenu.style.display = 'none';
    } else {
      // Show login button
      authBtn.textContent = 'Iniciar sesión';
      dashboardLink.style.display = 'none';
      dashboardMenuLink.style.display = 'none';

      if (userMenu) userMenu.style.display = 'none';
    }
  }

  /**
   * Update nav links active state
   */
  updateNavLinks() {
    document.querySelectorAll('[data-page]').forEach(link => {
      link.classList.remove('navbar__link--active');
    });

    const currentPage = router.getCurrentPage();
    const activeLink = document.querySelector(`[data-page="${currentPage}"]`);
    if (activeLink) {
      activeLink.classList.add('navbar__link--active');
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
