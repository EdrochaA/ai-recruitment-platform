/**
 * Configuration Module
 * Centralized configuration for the application
 */

const CONFIG = {
  // API Configuration
  API_BASE_URL: localStorage.getItem('apiBaseUrl') || 'http://ai-recruitment-platform-env.eba-vib3ka2v.eu-west-1.elasticbeanstalk.com',
  
  // Application Info
  APP_NAME: 'AI Recruitment Platform',
  
  // Endpoints
  ENDPOINTS: {
    JOB_OFFERS: '/job-offers',
    APPLICATIONS: '/applications',
  },
  
  // UI Settings
  ITEMS_PER_PAGE: 10,
  TIMEOUT: 10000,
};

// Make CONFIG available globally
window.CONFIG = CONFIG;
