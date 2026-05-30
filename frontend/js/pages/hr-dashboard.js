/**
 * HR Dashboard Module
 * Allows HR users to manage job offers and view applications
 */

let hrJobs = [];
let selectedJobId = null;
let allApplications = {};

/**
 * Initialize HR dashboard
 */
window.initHrDashboard = async function() {
  loadHRJobs();
  setupTabs();
  setupCreateOfferForm();
  setupDetailsPanel();
};

/**
 * Load HR's job offers
 */
async function loadHRJobs() {
  try {
    UI.showLoading();
    const response = await apiClient.getJobOffers();
    hrJobs = response.offers || [];
    
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

  // Add click listeners to all cards
  container.querySelectorAll('.job-card').forEach(card => {
    card.addEventListener('click', (e) => {
      const jobId = e.currentTarget.dataset.jobId;
      showOfferDetails(jobId);
    });
  });
}

/**
 * Create offer card
 */
function createOfferCard(job) {
  return `
    <div class="job-card" data-job-id="${job.id}" style="cursor: pointer;">
      <h3 class="job-card__title">${Format.truncate(job.title, 50)}</h3>
      <div class="job-card__location">
        📍 ${job.location}
      </div>
      <p class="job-card__description">${Format.truncate(job.description, 100)}</p>
      <div class="job-card__footer">
        <div class="job-card__meta">
          <span class="badge badge--${job.status?.toLowerCase() || 'open'}">${job.status || 'Abierta'}</span>
          <span style="font-size: 0.75rem; color: var(--gray-500);">ID: ${job.id.substring(0, 8)}</span>
        </div>
      </div>
      <div style="font-size: 0.85rem; color: var(--primary); margin-top: 8px;">
        Haz clic para ver detalles →
      </div>
    </div>
  `;
}

/**
 * Setup tabs
 */
function setupTabs() {
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.onclick = function(e) {
      e.preventDefault();
      const targetTab = e.currentTarget.dataset.tab;
      switchTab(targetTab);
      return false;
    };
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
    form.onsubmit = async function(e) {
      e.preventDefault();
      await handleCreateOffer();
      return false;
    };
  }
}

/**
 * Setup details panel
 */
function setupDetailsPanel() {
  const detailsPanel = document.getElementById('offer-details-panel');
  const closeBtn = document.getElementById('details-panel-close');
  
  if (closeBtn) {
    closeBtn.onclick = function(e) {
      e.preventDefault();
      closeOfferDetails();
      return false;
    };
  }
  
  // Close when clicking outside
  if (detailsPanel) {
    detailsPanel.onclick = function(e) {
      if (e.target === detailsPanel) {
        closeOfferDetails();
      }
    };
  }
}

/**
 * Show offer details in panel
 */
async function showOfferDetails(jobId) {
  selectedJobId = jobId;
  const job = hrJobs.find(j => j.id === jobId);
  
  if (!job) return;
  
  // Load applications
  try {
    UI.showLoading();
    const applications = await apiClient.getApplicationsByJobOffer(jobId);
    allApplications[jobId] = applications || [];
    UI.hideLoading();
  } catch (error) {
    console.error('Error loading applications:', error);
    allApplications[jobId] = [];
    UI.hideLoading();
  }
  
  // Render the details panel
  renderOfferDetailsPanel(job);
  
  // Show panel
  const panel = document.getElementById('offer-details-panel');
  if (panel) {
    panel.style.display = 'flex';
  }
}

/**
 * Close offer details panel
 */
function closeOfferDetails() {
  const panel = document.getElementById('offer-details-panel');
  if (panel) {
    panel.style.display = 'none';
  }
  selectedJobId = null;
}

/**
 * Render offer details panel
 */
function renderOfferDetailsPanel(job) {
  const contentDiv = document.getElementById('offer-details-content');
  if (!contentDiv) return;
  
  const applications = allApplications[job.id] || [];
  
  const applicationsHtml = applications.length > 0 ? `
    <div class="offer-detail__section">
      <h3>Candidaturas (${applications.length})</h3>
      <table class="applications-table" style="width: 100%; margin-top: 10px;">
        <thead>
          <tr>
            <th>Candidato</th>
            <th>Email</th>
            <th>CV</th>
            <th>Tamaño</th>
            <th>Fecha</th>
            <th>Estado CV</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${applications.map(app => `
            <tr>
              <td>${app.candidate_name}</td>
              <td>${app.candidate_email}</td>
              <td>${app.cv_original_filename ? `<strong>${app.cv_original_filename}</strong>` : '-'}</td>
              <td>${app.cv_size_bytes ? Format.fileSize(app.cv_size_bytes) : '-'}</td>
              <td>${Format.dateTime(app.cv_uploaded_at || app.created_at)}</td>
              <td>${getStatusBadge(app.cv_processing_status || 'pending')}</td>
              <td>
                ${app.cv_storage_key ? `<button class="btn btn--secondary" onclick="openApplicationCV('${app.id}')">Abrir CV</button>` : '-'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  ` : `
    <div class="offer-detail__section">
      <p style="color: var(--gray-500); text-align: center; padding: 20px;">
        No hay candidaturas aún para esta oferta
      </p>
    </div>
  `;
  
  const content = `
    <div class="offer-detail">
      <div class="offer-detail__header">
        <div>
          <h2>${job.title}</h2>
          <p class="offer-detail__company">${job.company}</p>
        </div>
        <span class="badge badge--${job.status?.toLowerCase() || 'open'}">${job.status || 'Abierta'}</span>
      </div>
      
      <div class="offer-detail__sections">
        <div class="offer-detail__section">
          <h3>Información General</h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
              <strong>Ubicación:</strong>
              <p>${job.location}</p>
            </div>
            <div>
              <strong>Tipo de empleo:</strong>
              <p>${job.employment_type || '-'}</p>
            </div>
            <div>
              <strong>Salario:</strong>
              <p>${job.salary_min && job.salary_max ? `${job.salary_min} - ${job.salary_max} ${job.currency}` : '-'}</p>
            </div>
            <div>
              <strong>Fecha de creación:</strong>
              <p>${Format.date(job.created_at)}</p>
            </div>
          </div>
        </div>
        
        <div class="offer-detail__section">
          <h3>Descripción</h3>
          <p>${job.description}</p>
        </div>
        
        ${job.required_skills && job.required_skills.length > 0 ? `
        <div class="offer-detail__section">
          <h3>Habilidades Requeridas</h3>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${job.required_skills.map(skill => `
              <span class="badge badge--secondary">${skill}</span>
            `).join('')}
          </div>
        </div>
        ` : ''}
        
        <div class="offer-detail__section">
          <h3>Acciones</h3>
          <div style="display: flex; gap: 10px;">
            <button class="btn btn--secondary" onclick="closeOfferDetails()">Cerrar Panel</button>
            ${job.status === 'open' ? `
              <button class="btn btn--warning" onclick="closeOfferStatus()">Cerrar Oferta</button>
            ` : ''}
          </div>
        </div>
        
        ${applicationsHtml}
      </div>
    </div>
  `;
  
  contentDiv.innerHTML = content;
}

window.openApplicationCV = async function(applicationId) {
  if (!apiClient || typeof apiClient.openCV !== 'function') {
    UI.showError('La descarga de CV no está disponible todavía en el backend.');
    return;
  }

  try {
    await apiClient.openCV(applicationId);
  } catch (error) {
    console.error('Error opening CV:', error);
    if (error?.status === 404) {
      UI.showError('El endpoint de descarga o el CV no está disponible todavía.');
      return;
    }

    UI.showError(error.message || 'No se pudo abrir el CV');
  }
};

/**
 * Close offer status
 */
async function closeOfferStatus() {
  if (!selectedJobId) return;
  
  if (!confirm('¿Seguro que deseas cerrar esta oferta? Los candidatos no podrán aplicar')) {
    return;
  }
  
  // TODO: Implement close offer endpoint
  UI.showSuccess('Oferta cerrada correctamente');
  closeOfferDetails();
  loadHRJobs();
}

/**
 * Handle create offer
 */
async function handleCreateOffer() {
  const titleInput = document.getElementById('offer-title');
  const companyInput = document.getElementById('offer-company');
  const locationInput = document.getElementById('offer-location');
  const descriptionInput = document.getElementById('offer-description');
  const employmentTypeSelect = document.getElementById('offer-employment-type');
  const salaryMinInput = document.getElementById('offer-salary-min');
  const salaryMaxInput = document.getElementById('offer-salary-max');
  const requiredSkillsInput = document.getElementById('offer-required-skills');
  const niceSkillsInput = document.getElementById('offer-nice-skills');

  // Validate required fields
  if (!titleInput.value.trim() || !companyInput.value.trim() || !locationInput.value.trim() || !descriptionInput.value.trim()) {
    UI.showError('Título, empresa, ubicación y descripción son requeridos');
    return;
  }

  try {
    UI.showLoading();

    // Parse skills
    const requiredSkills = requiredSkillsInput.value
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);
    
    const niceSkills = niceSkillsInput.value
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const offerData = {
      title: titleInput.value.trim(),
      company: companyInput.value.trim(),
      location: locationInput.value.trim(),
      description: descriptionInput.value.trim(),
      employment_type: employmentTypeSelect.value,
      salary_min: parseFloat(salaryMinInput.value) || 0,
      salary_max: parseFloat(salaryMaxInput.value) || 0,
      required_skills: requiredSkills,
      nice_to_have_skills: niceSkills,
    };

    const newOffer = await apiClient.createJobOffer(offerData);

    UI.hideLoading();
    UI.showSuccess('¡Oferta de trabajo creada exitosamente!');

    // Reset form
    document.getElementById('create-offer-form').reset();

    // Reload offers
    loadHRJobs();
  } catch (error) {
    UI.hideLoading();
    console.error('Error creating offer:', error);
    UI.showError(error.message || 'Error al crear la oferta. Intenta de nuevo.');
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
          <th>Tamaño</th>
          <th>Fecha</th>
          <th>Estado CV</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        ${applications.map(app => `
          <tr>
            <td>${app.candidate_name}</td>
            <td>${app.candidate_email}</td>
            <td>${app.cv_original_filename ? `<strong>${app.cv_original_filename}</strong>` : '-'}</td>
            <td>${app.cv_size_bytes ? Format.fileSize(app.cv_size_bytes) : '-'}</td>
            <td>${Format.dateTime(app.cv_uploaded_at || app.created_at)}</td>
            <td>${getStatusBadge(app.cv_processing_status || 'pending')}</td>
            <td>
              ${app.cv_storage_key ? `<button class="btn btn--secondary" onclick="openApplicationCV('${app.id}')">Abrir CV</button>` : '-'}
            </td>
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
