/**
 * Authentication System - Using Backend API + MongoDB
 * Real authentication with JWT tokens from backend
 */

class BackendAuthSystem {
  constructor() {
    this.STORAGE_KEY = 'ai_recruitment_auth';
    this.API_BASE_URL = window.CONFIG?.API_BASE_URL || 'http://localhost:8000';
  }

  /**
   * Login with MongoDB backend
   */
  async login(email, password) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'Email o contraseña incorrectos',
        };
      }

      const data = await response.json();

      // Save token and user info to localStorage
      const session = {
        userId: data.user.id,
        email: data.user.email,
        name: data.user.name,
        role: data.user.role,
        access_token: data.access_token,
        loginTime: new Date().toISOString(),
      };

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
      window.dispatchEvent(new Event('authChange'));

      return {
        success: true,
        user: {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          role: data.user.role,
        },
      };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: 'Error de conexión. Verifica que el backend esté ejecutándose.',
      };
    }
  }

  /**
   * Signup with MongoDB backend
   */
  async signup(name, email, password) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name,
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'Error al crear la cuenta',
        };
      }

      const data = await response.json();

      // Save token and user info to localStorage
      const session = {
        userId: data.user.id,
        email: data.user.email,
        name: data.user.name,
        role: data.user.role,
        access_token: data.access_token,
        loginTime: new Date().toISOString(),
      };

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
      window.dispatchEvent(new Event('authChange'));

      return {
        success: true,
        user: {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          role: data.user.role,
        },
      };
    } catch (error) {
      console.error('Signup error:', error);
      return {
        success: false,
        error: 'Error de conexión. Verifica que el backend esté ejecutándose.',
      };
    }
  }

  /**
   * Logout - clear session
   */
  logout() {
    localStorage.removeItem(this.STORAGE_KEY);
    window.dispatchEvent(new Event('authChange'));
  }

  /**
   * Get current authenticated user
   */
  getCurrentUser() {
    const session = localStorage.getItem(this.STORAGE_KEY);
    
    if (!session) {
      return null;
    }

    try {
      return JSON.parse(session);
    } catch (e) {
      return null;
    }
  }

  /**
   * Get JWT token
   */
  getToken() {
    const user = this.getCurrentUser();
    return user ? user.access_token : null;
  }

  /**
   * Check if authenticated
   */
  isAuthenticated() {
    return this.getCurrentUser() !== null;
  }

  /**
   * Check if user has specific role
   */
  hasRole(role) {
    const user = this.getCurrentUser();
    return user && user.role === role;
  }

  /**
   * Check if is admin
   */
  isAdmin() {
    return this.hasRole('admin');
  }

  /**
   * Check if is HR
   */
  isHR() {
    return this.hasRole('hr');
  }

  /**
   * Check if is candidate
   */
  isCandidate() {
    return this.hasRole('candidate');
  }

  /**
   * Create HR user (admin only) - via backend
   */
  async createHRUser(name, email, password) {
    const token = this.getToken();
    
    if (!token) {
      return {
        success: false,
        error: 'No autenticado',
      };
    }

    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/admin/create-user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: name,
          email: email,
          password: password,
          role: 'hr',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'Error al crear usuario HR',
        };
      }

      const data = await response.json();

      return {
        success: true,
        user: {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          role: data.user.role,
        },
      };
    } catch (error) {
      console.error('Create HR user error:', error);
      return {
        success: false,
        error: 'Error de conexión',
      };
    }
  }
}

// Initialize
const authSystem = new BackendAuthSystem();
window.authSystem = authSystem;
