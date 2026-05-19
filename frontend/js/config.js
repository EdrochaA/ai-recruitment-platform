/**
 * Configuration Module
 * Centralized configuration for the application
 */

const CONFIG = {
  // API Configuration
  API_BASE_URL: localStorage.getItem('apiBaseUrl') || 'http://localhost:8000',
  
  // Application Info
  APP_NAME: 'AI Recruitment Platform',
  
  // Mock Auth Settings
  ENABLE_MOCK_AUTH: true,
  
  // Endpoints
  ENDPOINTS: {
    JOB_OFFERS: '/job-offers',
    APPLICATIONS: '/applications',
  },
  
  // UI Settings
  ITEMS_PER_PAGE: 10,
  TIMEOUT: 10000,
};

// Allow configuration override via localStorage or environment
window.CONFIG = CONFIG;

export default CONFIG;
