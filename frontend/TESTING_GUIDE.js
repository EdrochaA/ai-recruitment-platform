/**
 * Testing & Demo Guide
 * Copy-paste commands in browser console (F12) to test features
 */

// ============================================
// AUTHENTICATION TESTS
// ============================================

// Test Login
authSystem.login('admin@example.com', 'admin123');
// Expected: { success: true, user: {...} }

// Test signup
authSystem.signup('John Doe', 'john@example.com', 'password123', 'candidate');
// Expected: { success: true, user: {...} }

// Check current user
authSystem.getCurrentUser();
// Expected: { userId, email, name, role, loginTime }

// Logout
authSystem.logout();
// Expected: { success: true }

// ============================================
// API TESTS
// ============================================

// Get all job offers
await apiClient.getJobOffers();

// Create job offer
await apiClient.createJobOffer(
  'Full Stack Developer',
  'Madrid, Spain',
  'We are looking for an experienced developer...'
);

// Get offer ID first
const offers = await apiClient.getJobOffers();
const offerId = offers[0].id;

// Create application
await apiClient.createApplication(
  offerId,
  'John Developer',
  'john.dev@example.com'
);

// Get applications for offer
await apiClient.getApplicationsByJobOffer(offerId);

// ============================================
// UI TESTS
// ============================================

// Show success message
UI.showSuccess('This is a success message');

// Show error message
UI.showError('This is an error message');

// Show loading
UI.showLoading();
setTimeout(() => UI.hideLoading(), 2000);

// ============================================
// NAVIGATION TESTS
// ============================================

// Navigate to home
router.navigate('home');

// Navigate to job detail
const offers = await apiClient.getJobOffers();
router.navigate('job-detail', { job: offers[0] });

// Navigate to HR dashboard (requires HR auth)
authSystem.login('hr@example.com', 'hr123');
router.navigate('hr-dashboard');

// Navigate to admin dashboard (requires admin auth)
authSystem.login('admin@example.com', 'admin123');
router.navigate('admin-dashboard');

// ============================================
// UTILITY TESTS
// ============================================

// Format date
Format.date('2024-05-19T10:30:00');

// Format file size
Format.fileSize(1024 * 1024); // 1 MB

// Truncate text
Format.truncate('This is a very long text that should be truncated', 30);

// Validate email
Validation.isValidEmail('test@example.com');

// ============================================
// DEBUGGING
// ============================================

// Check current page
router.getCurrentPage();

// Clear all caches
Storage.clearAllCaches();

// Check API base URL
console.log(apiClient.baseURL);

// List all users (admin only)
authSystem.getAllUsers();

// Get all HR users (admin only)
authSystem.getHRUsers();

// ============================================
// DEMO SCENARIO - FULL FLOW
// ============================================

// 1. Create HR user and login
authSystem.signup('Jane HR', 'jane.hr@example.com', 'hr123pass', 'hr');
authSystem.logout();

// 2. Admin creates HR user
authSystem.login('admin@example.com', 'admin123');
authSystem.createHRUser('Bob HR', 'bob.hr@example.com', 'bobpass123');

// 3. HR user creates job offer
authSystem.logout();
authSystem.login('jane.hr@example.com', 'hr123pass');
const newOffer = await apiClient.createJobOffer(
  'Senior React Developer',
  'Barcelona, Spain',
  'Looking for a Senior React Developer with 5+ years experience'
);

// 4. Candidate applies
authSystem.logout();
const candidateSignup = authSystem.signup(
  'Alice Developer',
  'alice@example.com',
  'alicepass123',
  'candidate'
);

// 5. Get offers
const allOffers = await apiClient.getJobOffers();
console.log('Available offers:', allOffers);

// 6. Create application
const app = await apiClient.createApplication(
  allOffers[0].id,
  'Alice Developer',
  'alice@example.com'
);

// 7. HR views applications
authSystem.logout();
authSystem.login('jane.hr@example.com', 'hr123pass');
const applications = await apiClient.getApplicationsByJobOffer(allOffers[0].id);
console.log('Applications:', applications);
