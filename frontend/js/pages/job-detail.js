/**
 * Job Detail Page Module
 * Displays detailed information about a job offer
 */

let currentJob = null;

/**
 * Initialize job detail page
 */
window.initJobDetail = function(params) {
  if (params.job) {
    currentJob = params.job;
  }

  renderJobDetail();
  setupDeleteButton();
  setupBackButton();
};

/**
 * Render job detail
 */
function renderJobDetail() {
  if (!currentJob) {
    UI.showError('Oferta no encontrada');
    router.navigate('home');
    return;
  }

  const titleEl = document.getElementById('job-title');
  const locationEl = document.getElementById('job-location');
  const statusEl = document.getElementById('job-status');
  const descriptionEl = document.getElementById('job-description');
  const applySectionEl = document.getElementById('apply-section');

  titleEl.textContent = currentJob.title;
  locationEl.textContent = `📍 ${currentJob.location}`;
  statusEl.textContent = currentJob.status || 'Abierta';
  descriptionEl.textContent = currentJob.description;

  // Render apply section based on auth status
  renderApplySection(applySectionEl);
}

/**
 * Render apply section
 */
function renderApplySection(container) {
  const isAuthenticated = authSystem.isAuthenticated();
  const isCandidate = authSystem.isCandidate();

  if (!isAuthenticated) {
    container.innerHTML = `
      <div class="alert alert--error" style="margin-top: 2rem;">
        <p>Debes <button class="btn btn--link" id="login-for-apply">iniciar sesión</button> para aplicar a esta oferta.</p>
      </div>
    `;
    document.getElementById('login-for-apply').addEventListener('click', () => {
      router.showAuthModal();
    });
  } else if (isCandidate) {
    container.innerHTML = `
      <button class="btn btn--primary btn--full" id="apply-btn" style="margin-top: 2rem;">
        Aplicar a esta oferta
      </button>
    `;
    document.getElementById('apply-btn').addEventListener('click', () => {
      router.navigate('apply', { job: currentJob });
    });
  } else {
    container.innerHTML = `
      <div class="alert alert--error" style="margin-top: 2rem;">
        <p>Solo los candidatos pueden aplicar a ofertas. Tu cuenta es de tipo: <strong>${authSystem.getCurrentUser().role}</strong></p>
      </div>
    `;
  }
}

/**
 * Setup delete button
 */
function setupDeleteButton() {
  // Only show delete option to HR who created it
  // For now, we would need to track creator - skipping for MVP
}

/**
 * Setup back button
 */
function setupBackButton() {
  const backBtn = document.getElementById('back-button');
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      router.navigate('home');
    });
  }
}
