/**
 * Mock Authentication System
 * Temporary client-side only authentication for development/demo
 * This is NOT for production use - Cognito integration pending
 */

class MockAuthSystem {
  constructor() {
    this.STORAGE_KEY = 'ai_recruitment_auth';
    this.USERS_KEY = 'ai_recruitment_users';
    
    // Initialize default mock users
    this.initializeDefaultUsers();
  }

  /**
   * Initialize default mock users for testing
   */
  initializeDefaultUsers() {
    const existingUsers = this.getAllUsers();
    
    // Only add defaults if no users exist
    if (Object.keys(existingUsers).length === 0) {
      const defaultUsers = {
        'admin@example.com': {
          id: 'admin-001',
          email: 'admin@example.com',
          name: 'Admin User',
          password: 'admin123',
          role: 'admin',
          createdAt: new Date().toISOString(),
        },
        'hr@example.com': {
          id: 'hr-001',
          email: 'hr@example.com',
          name: 'HR Manager',
          password: 'hr123',
          role: 'hr',
          createdAt: new Date().toISOString(),
        },
        'candidate@example.com': {
          id: 'candidate-001',
          email: 'candidate@example.com',
          name: 'Candidate Demo',
          password: 'candidate123',
          role: 'candidate',
          createdAt: new Date().toISOString(),
        },
      };
      
      localStorage.setItem(this.USERS_KEY, JSON.stringify(defaultUsers));
    }
  }

  /**
   * Login - authenticate user
   */
  login(email, password) {
    const users = this.getAllUsers();
    const user = users[email];

    if (!user || user.password !== password) {
      return {
        success: false,
        error: 'Correo o contraseña incorrectos',
      };
    }

    // Create session
    const session = {
      userId: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      loginTime: new Date().toISOString(),
    };

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
    window.dispatchEvent(new Event('authChange'));

    return {
      success: true,
      user: this.getCurrentUser(),
    };
  }

  /**
   * Signup - create new user account
   */
  signup(name, email, password, role) {
    const users = this.getAllUsers();

    if (users[email]) {
      return {
        success: false,
        error: 'Este correo ya está registrado',
      };
    }

    if (!['candidate', 'hr'].includes(role)) {
      return {
        success: false,
        error: 'Tipo de usuario inválido',
      };
    }

    const newUser = {
      id: `user-${Date.now()}`,
      email,
      name,
      password,
      role,
      createdAt: new Date().toISOString(),
    };

    users[email] = newUser;
    localStorage.setItem(this.USERS_KEY, JSON.stringify(users));

    // Auto-login after signup
    return this.login(email, password);
  }

  /**
   * Logout - clear session
   */
  logout() {
    localStorage.removeItem(this.STORAGE_KEY);
    window.dispatchEvent(new Event('authChange'));
    return { success: true };
  }

  /**
   * Get current user from session
   */
  getCurrentUser() {
    const session = localStorage.getItem(this.STORAGE_KEY);
    return session ? JSON.parse(session) : null;
  }

  /**
   * Check if user is authenticated
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
   * Check if user is admin
   */
  isAdmin() {
    return this.hasRole('admin');
  }

  /**
   * Check if user is HR
   */
  isHR() {
    return this.hasRole('hr');
  }

  /**
   * Check if user is candidate
   */
  isCandidate() {
    return this.hasRole('candidate');
  }

  /**
   * Get all users (for admin purposes)
   */
  getAllUsers() {
    const usersJson = localStorage.getItem(this.USERS_KEY);
    return usersJson ? JSON.parse(usersJson) : {};
  }

  /**
   * Create HR user (admin only)
   */
  createHRUser(name, email, password) {
    if (!this.isAdmin()) {
      return {
        success: false,
        error: 'Solo administradores pueden crear usuarios HR',
      };
    }

    return this.signup(name, email, password, 'hr');
  }

  /**
   * Get HR users associated with current user (if admin)
   */
  getHRUsers() {
    if (!this.isAdmin()) {
      return [];
    }

    const users = this.getAllUsers();
    return Object.values(users).filter(u => u.role === 'hr');
  }
}

// Export singleton instance
const authSystem = new MockAuthSystem();
window.authSystem = authSystem;
