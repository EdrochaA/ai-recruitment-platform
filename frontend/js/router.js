/**
 * Router Module
 * Handles page navigation and routing logic.
 */

class Router {
  constructor() {
    this.currentPage = 'home';
    this.routes = new Map();
    this.registerDefaultRoutes();
  }

  /**
   * Register default routes.
   * - navTitle: label shown in the topbar for this route.
   * - requiresRoles: array of roles allowed (any match). Preferred.
   * - requiresRole: single role (legacy, still supported).
   */
  registerDefaultRoutes() {
    this.register('home', {
      title: 'Inicio - TalentoIA',
      navTitle: 'Inicio / Ofertas',
      element: 'home-page',
      requiresAuth: false,
    });

    this.register('job-detail', {
      title: 'Detalle de Oferta - TalentoIA',
      navTitle: 'Detalle de Oferta',
      element: 'job-detail-page',
      requiresAuth: false,
    });

    this.register('apply', {
      title: 'Aplicar a Oferta - TalentoIA',
      navTitle: 'Aplicar a Oferta',
      element: 'apply-page',
      requiresAuth: true,
      requiresRoles: ['candidate'],
    });

    this.register('hr-dashboard', {
      title: 'Dashboard HR - TalentoIA',
      navTitle: 'Panel HR',
      element: 'hr-dashboard-page',
      requiresAuth: true,
      requiresRoles: ['hr', 'admin'],
    });

    this.register('admin-dashboard', {
      title: 'Panel de Administrador - TalentoIA',
      navTitle: 'Panel Admin',
      element: 'admin-dashboard-page',
      requiresAuth: true,
      requiresRoles: ['admin'],
    });

    this.register('chat', {
      title: 'Asistente IA - TalentoIA',
      navTitle: 'Asistente IA',
      element: 'chat-page',
      requiresAuth: true,
      requiresRoles: ['hr', 'admin'],
    });
  }

  /**
   * Register a route
   */
  register(name, config) {
    this.routes.set(name, config);
  }

  /**
   * Check whether the current user satisfies a route's role requirements.
   */
  isRoleAllowed(route) {
    // New-style: array of allowed roles
    if (Array.isArray(route.requiresRoles) && route.requiresRoles.length > 0) {
      const user = authSystem.getCurrentUser();
      return !!user && route.requiresRoles.includes(user.role);
    }
    // Legacy: single role
    if (route.requiresRole) {
      return authSystem.hasRole(route.requiresRole);
    }
    return true;
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
    if (route.requiresAuth && !this.isRoleAllowed(route)) {
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

      // Update document title
      document.title = route.title;

      // Keep navigation state in sync even if page initialization fails.
      window.app?.updateNavLinks?.();

      // Call page-specific init if available (e.g. initChat, initHrDashboard)
      const initFunctionName = 'init' + routeName.split('-').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('');
      if (window[initFunctionName]) {
        window[initFunctionName](params);
      }

      // Scroll content to top
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
