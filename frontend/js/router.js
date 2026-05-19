/**
 * Router Module
 * Handles page navigation and routing logic
 */

class Router {
  constructor() {
    this.currentPage = 'home';
    this.routes = new Map();
    this.registerDefaultRoutes();
  }

  /**
   * Register default routes
   */
  registerDefaultRoutes() {
    this.register('home', {
      title: 'Inicio - AI Recruitment Platform',
      element: 'home-page',
      requiresAuth: false,
    });

    this.register('job-detail', {
      title: 'Detalle de Oferta',
      element: 'job-detail-page',
      requiresAuth: false,
    });

    this.register('apply', {
      title: 'Aplicar a Oferta',
      element: 'apply-page',
      requiresAuth: true,
      requiresRole: 'candidate',
    });

    this.register('hr-dashboard', {
      title: 'Dashboard HR',
      element: 'hr-dashboard-page',
      requiresAuth: true,
      requiresRole: 'hr',
    });

    this.register('admin-dashboard', {
      title: 'Panel de Administrador',
      element: 'admin-dashboard-page',
      requiresAuth: true,
      requiresRole: 'admin',
    });
  }

  /**
   * Register a route
   */
  register(name, config) {
    this.routes.set(name, config);
  }

  /**
   * Navigate to a page
   */
  navigate(routeName, params = {}) {
    const route = this.routes.get(routeName);

    if (!route) {
      console.error(`Route not found: ${routeName}`);
      UI.showError('Página no encontrada');
      return false;
    }

    // Check authentication
    if (route.requiresAuth && !authSystem.isAuthenticated()) {
      UI.showError('Debes iniciar sesión para acceder a esta página');
      this.showAuthModal();
      return false;
    }

    // Check role
    if (route.requiresRole && !authSystem.hasRole(route.requiresRole)) {
      UI.showError('No tienes permiso para acceder a esta página');
      return false;
    }

    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
      page.classList.remove('page--active');
    });

    // Show target page
    const targetElement = document.getElementById(route.element);
    if (targetElement) {
      targetElement.classList.add('page--active');
      this.currentPage = routeName;

      // Update title
      document.title = route.title;

      // Call page-specific init if available
      if (window[`init${routeName.charAt(0).toUpperCase()}${routeName.slice(1)}`]) {
        window[`init${routeName.charAt(0).toUpperCase()}${routeName.slice(1)}`](params);
      }

      // Scroll to top
      window.scrollTo(0, 0);

      return true;
    }

    return false;
  }

  /**
   * Show auth modal
   */
  showAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
  }

  /**
   * Close auth modal
   */
  closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
  }

  /**
   * Get current page
   */
  getCurrentPage() {
    return this.currentPage;
  }

  /**
   * Get route config
   */
  getRoute(name) {
    return this.routes.get(name);
  }
}

// Export singleton instance
const router = new Router();
window.router = router;

