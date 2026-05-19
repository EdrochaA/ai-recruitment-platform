/**
 * HR Dashboard Module
 * Allows HR users to manage job offers and view applications
 */

let hrJobs = [];
let allApplications = {};

/**
 * Initialize HR dashboard
 */
window.initHrDashboard = async function() {
  loadHRJobs();
  setupTabs();
  setupCreateOfferForm();
};

/**
 * Load HR's job offers
 */
async function loadHRJobs() {
  try {
    UI.showLoading();
    const jobs = await apiClient.getJobOffers();
    hrJobs = jobs || [];
    
    // For MVP, all jobs are shown to all HR users
    // In production, would filter by creator
    
    renderMyOffers();
    UI.hideLoading();
  } catch (error) {
    UI.hideLoading();
    console.error('Error loading HR jobs:', error);
    UI.showError('Error al cargar las ofertas. Intenta de nuevo.');
  }
}

/**
 * Render my offers
 */
function renderMyOffers() {
  const container = document.getElementById('my-offers-list');
  const emptyState = document.getElementById('my-offers-empty');

  if (hrJobs.length === 0) {
    container.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';
  container.innerHTML = hrJobs.map(job => createOfferCard(job)).join('');

  // Add event listeners
  container.querySelectorAll('[data-action="view-applications"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const jobId = e.currentTarget.dataset.jobId;
      selectTabAndLoadApplications('applications', jobId);
    });
  });
}

/**
 * Create offer card
 */
function createOfferCard(job) {
  return `
    <div class="job-card">
      <h3 class="job-card__title">${Format.truncate(job.title, 50)}</h3>
      <div class="job-card__location">
        📍 ${job.location}
      </div>
      <p class="job-card__description">${Format.truncate(job.description, 100)}</p>
      <div class="job-card__footer">
        <div class="job-card__meta">
          <span class="badge">${job.status || 'Abierta'}</span>
          <span style="font-size: 0.75rem; color: var(--gray-500);">ID: ${job.id.substring(0, 8)}</span>
        </div>
        <button class="btn btn--secondary" data-action="view-applications" data-job-id="${job.id}">
          Ver candidaturas
        </button>
      </div>
    </div>
  `;
}

/**
 * Setup tabs
 */
function setupTabs() {
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetTab = e.currentTarget.dataset.tab;
      switchTab(targetTab);
    });
  });
}

/**
 * Switch tab
 */
function switchTab(tabName) {
  // Update button states
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.classList.remove('tab-button--active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('tab-button--active');

  // Update content visibility
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('tab-content--active');
  });
  document.getElementById(`${tabName}-tab`).classList.add('tab-content--active');

  // Load data if needed
  if (tabName === 'my-offers') {
    renderMyOffers();
  }
}

/**
 * Select tab and load applications
 */
function selectTabAndLoadApplications(tabName, jobId) {
  switchTab(tabName);
  loadApplicationsForJob(jobId);
}

/**
 * Setup create offer form
 */
function setupCreateOfferForm() {
  const form = document.getElementById('create-offer-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await handleCreateOffer();
    });
  }
}

/**
 * Handle create offer
 */
async function handleCreateOffer() {
  const titleInput = document.getElementById('offer-title');
  const locationInput = document.getElementById('offer-location');
  const descriptionInput = document.getElementById('offer-description');

  // Validate
  if (!titleInput.value.trim() || !locationInput.value.trim() || !descriptionInput.value.trim()) {
    UI.showError('Todos los campos son requeridos');
    return;
  }

  try {
    UI.showLoading();

    const newOffer = await apiClient.createJobOffer(
      titleInput.value.trim(),
      locationInput.value.trim(),
      descriptionInput.value.trim()
    );

    UI.hideLoading();
    UI.showSuccess('¡Oferta de trabajo creada exitosamente!');

    // Reset form
    UI.clearForm('create-offer-form');

    // Reload offers
    loadHRJobs();
  } catch (error) {
    UI.hideLoading();
    console.error('Error creating offer:', error);
    UI.showError('Error al crear la oferta. Intenta de nuevo.');
  }
}

/**
 * Load applications for a job
 */
async function loadApplicationsForJob(jobId) {
  try {
    UI.showLoading();

    const applications = await apiClient.getApplicationsByJobOffer(jobId);
    allApplications[jobId] = applications || [];

    renderApplications(jobId);
    UI.hideLoading();
  } catch (error) {
    UI.hideLoading();
    console.error('Error loading applications:', error);
    UI.showError('Error al cargar las candidaturas. Intenta de nuevo.');
  }
}

/**
 * Render applications
 */
function renderApplications(jobId) {
  const container = document.getElementById('applications-list');
  const emptyState = document.getElementById('applications-empty');
  const applications = allApplications[jobId] || [];

  if (applications.length === 0) {
    container.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';

  const html = `
    <table class="applications-table">
      <thead>
        <tr>
          <th>Candidato</th>
          <th>Correo</th>
          <th>CV</th>
          <th>Estado CV</th>
          <th>Fecha</th>
        </tr>
      </thead>
      <tbody>
        ${applications.map(app => `
          <tr>
            <td>${app.candidate_name}</td>
            <td>${app.candidate_email}</td>
            <td>${app.cv_original_filename ? `<strong>${app.cv_original_filename}</strong>` : '-'}</td>
            <td>${getStatusBadge(app.cv_processing_status)}</td>
            <td>${Format.date(app.created_at)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
  const statusMap = {
    'pending': { label: 'Pendiente', class: 'badge' },
    'processing': { label: 'Procesando', class: 'badge badge--secondary' },
    'completed': { label: 'Completado', class: 'badge badge--success' },
    'failed': { label: 'Error', class: 'badge badge--error' },
  };

  const statusInfo = statusMap[status] || { label: status || 'Desconocido', class: 'badge' };
  return `<span class="${statusInfo.class}">${statusInfo.label}</span>`;
}
