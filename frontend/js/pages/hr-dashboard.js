/**
 * HR Dashboard Module
 * Allows HR users to manage job offers and view applications
 */

let hrJobs = [];
let selectedJobId = null;
let allApplications = {};
let myOffersSearchTerm = '';
let myOffersSearchTimeout = null;
let editingOfferId = null;

/**
 * Initialize HR dashboard
 */
window.initHrDashboard = async function() {
  loadHRJobs();
  setupTabs();
  setupCreateOfferForm();
  setupDetailsPanel();
  setupMyOffersSearch();
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
    showToast('Error al cargar las ofertas. Intenta de nuevo.', 'error');
  }
}

/**
 * Render my offers
 */
function renderMyOffers() {
  const container = document.getElementById('my-offers-list');
  const emptyState = document.getElementById('my-offers-empty');
  const filteredJobs = hrJobs.filter(job => {
    const searchable = `${job.title || ''} ${job.company || ''} ${job.location || ''}`.toLowerCase();
    return searchable.includes(myOffersSearchTerm);
  });

  if (filteredJobs.length === 0) {
    container.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';
  container.innerHTML = filteredJobs.map(job => createOfferCard(job)).join('');

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
  const isClosed = job.status === 'closed';

  return `
    <article class="job-card" data-job-id="${job.id}" style="cursor: pointer;">
      <header class="job-card__header" style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;">
        <h3 class="job-card__title">${Format.truncate(job.title, 50)}</h3>
        ${getOfferStatusBadge(job.status)}
      </header>
      <section class="job-card__body">
        <p class="job-card__location">📍 ${job.location || '-'}</p>
        <p class="job-card__description">${Format.truncate(job.description || '-', 100)}</p>
      </section>
      <footer class="job-card__footer" style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
        <div class="job-card__meta">
          <span style="color: var(--text-muted); font-size: 0.9rem;">${isClosed ? 'Oferta cerrada' : 'Oferta abierta'}</span>
        </div>
      </footer>
    </article>
  `;
}

function getOfferStatusBadge(status) {
  const isClosed = status === 'closed';
  const label = isClosed ? 'Cerrada' : 'Abierta';
  const className = isClosed ? 'badge badge--secondary' : 'badge badge--success';

  return `<span class="${className}">${label}</span>`;
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
      const clickedOverlay = e.target?.classList?.contains('modal__overlay');
      if (e.target === detailsPanel || clickedOverlay) {
        closeOfferDetails();
      }
    };
  }
}

function setupMyOffersSearch() {
  const searchInput = document.getElementById('my-offers-search');
  if (!searchInput) return;

  searchInput.addEventListener('input', (event) => {
    if (myOffersSearchTimeout) {
      clearTimeout(myOffersSearchTimeout);
    }

    const nextValue = (event.target.value || '').trim().toLowerCase();
    myOffersSearchTimeout = setTimeout(() => {
      myOffersSearchTerm = nextValue;
      renderMyOffers();
    }, 200);
  });
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
    const applicationsResponse = await apiClient.getApplicationsByJobOffer(jobId);
    const applications = Array.isArray(applicationsResponse) ? applicationsResponse : [];
    allApplications[jobId] = applications;
    console.log('Applications loaded:', applications);
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
  editingOfferId = null;
}

/**
 * Render offer details panel
 */
function renderOfferDetailsPanel(job) {
  const contentDiv = document.getElementById('offer-details-content');
  if (!contentDiv) return;
  
  const applications = allApplications[job.id] || [];
  const currentUser = authSystem.getCurrentUser();
  const canManageOffer = !!currentUser && ['hr', 'admin'].includes(currentUser.role);
  const isEditing = editingOfferId === job.id;
  console.log('Applications loaded:', applications);
  
  const applicationsHtml = applications.length > 0 ? `
    <div class="offer-detail__section">
      <h3>Candidaturas (${applications.length})</h3>
      <div class="applications-list" style="display: grid; gap: 10px; margin-top: 10px;">
        ${applications.map(app => `
          <article class="application-card" style="border: 1px solid var(--gray-200); border-radius: 8px; padding: 12px;">
            <h4 style="margin: 0 0 6px 0;">${app.candidate_name || '-'}</h4>
            <p style="margin: 2px 0;"><strong>Email:</strong> ${app.candidate_email || '-'}</p>
            <p style="margin: 2px 0;"><strong>CV:</strong> ${app.cv_original_filename || 'Sin CV'}</p>
            <p style="margin: 2px 0;"><strong>Tamaño:</strong> ${app.cv_size_bytes ? Format.fileSize(app.cv_size_bytes) : '-'}</p>
            <p style="margin: 2px 0;"><strong>Fecha:</strong> ${Format.dateTime(app.cv_uploaded_at || app.created_at)}</p>
            <p style="margin: 2px 0;"><strong>Estado:</strong> ${app.cv_processing_status || 'Pendiente'}</p>
            <div style="margin-top: 8px;">
              ${getCVActionHtml(app)}
            </div>
          </article>
        `).join('')}
      </div>
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
          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            ${applications.length > 0 ? `<button class="btn btn--primary" onclick="downloadAllCVs('${job.id}', '${job.title || 'oferta'}')">Descargar todos los CVs</button>` : ''}
            ${canManageOffer ? `<button class="btn btn--secondary" id="edit-offer-btn" type="button">Editar oferta</button>` : ''}
            ${canManageOffer ? `<button class="btn ${job.status === 'closed' ? 'btn--secondary' : 'btn--warning'}" id="toggle-offer-status-btn" type="button">${job.status === 'closed' ? 'Reabrir oferta' : 'Cerrar oferta'}</button>` : ''}
          </div>
        </div>

        ${canManageOffer ? `
        <div class="offer-detail__section">
          <h3>${isEditing ? 'Editar oferta' : 'Formulario de edición'}</h3>
          ${isEditing ? `
            <form id="edit-offer-form" class="form">
              <div class="form__group">
                <label for="edit-offer-title" class="form__label">Título del puesto</label>
                <input type="text" id="edit-offer-title" class="form__input" required>
              </div>

              <div class="form__group">
                <label for="edit-offer-company" class="form__label">Empresa</label>
                <input type="text" id="edit-offer-company" class="form__input" required>
              </div>

              <div class="form__group">
                <label for="edit-offer-location" class="form__label">Ubicación</label>
                <input type="text" id="edit-offer-location" class="form__input" required>
              </div>

              <div class="form__group">
                <label for="edit-offer-description" class="form__label">Descripción del puesto</label>
                <textarea id="edit-offer-description" class="form__textarea" required></textarea>
              </div>

              <div class="form__group">
                <label for="edit-offer-employment-type" class="form__label">Tipo de empleo</label>
                <select id="edit-offer-employment-type" class="form__input">
                  <option value="full-time">Tiempo completo</option>
                  <option value="part-time">Tiempo parcial</option>
                  <option value="contract">Contrato</option>
                  <option value="freelance">Freelance</option>
                </select>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="form__group">
                  <label for="edit-offer-salary-min" class="form__label">Salario mínimo (EUR)</label>
                  <input type="number" id="edit-offer-salary-min" class="form__input" min="0">
                </div>
                <div class="form__group">
                  <label for="edit-offer-salary-max" class="form__label">Salario máximo (EUR)</label>
                  <input type="number" id="edit-offer-salary-max" class="form__input" min="0">
                </div>
              </div>

              <div class="form__group">
                <label for="edit-offer-required-skills" class="form__label">Habilidades requeridas</label>
                <input type="text" id="edit-offer-required-skills" class="form__input" placeholder="Python, FastAPI, PostgreSQL">
              </div>

              <div class="form__group">
                <label for="edit-offer-nice-skills" class="form__label">Habilidades deseables</label>
                <input type="text" id="edit-offer-nice-skills" class="form__input" placeholder="Docker, Kubernetes, AWS">
              </div>

              <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button type="submit" class="btn btn--primary">Guardar cambios</button>
                <button type="button" class="btn btn--outline" id="cancel-edit-offer">Cancelar</button>
              </div>
            </form>
          ` : `
            <p style="color: var(--text-muted);">Pulsa en editar para modificar esta oferta sin salir del panel.</p>
          `}
        </div>
        ` : ''}
        
        ${applicationsHtml}
      </div>
    </div>
  `;
  
  contentDiv.innerHTML = content;

  if (canManageOffer) {
    document.getElementById('edit-offer-btn')?.addEventListener('click', () => {
      editingOfferId = job.id;
      renderOfferDetailsPanel(job);
    });

    document.getElementById('toggle-offer-status-btn')?.addEventListener('click', async () => {
      await closeOfferStatus(job);
    });

    if (isEditing) {
      setupEditOfferForm(job);
    }
  }
}

function setupEditOfferForm(job) {
  const form = document.getElementById('edit-offer-form');
  if (!form) return;

  document.getElementById('edit-offer-title').value = job.title || '';
  document.getElementById('edit-offer-company').value = job.company || '';
  document.getElementById('edit-offer-location').value = job.location || '';
  document.getElementById('edit-offer-description').value = job.description || '';
  document.getElementById('edit-offer-employment-type').value = job.employment_type || 'full-time';
  document.getElementById('edit-offer-salary-min').value = job.salary_min || '';
  document.getElementById('edit-offer-salary-max').value = job.salary_max || '';
  document.getElementById('edit-offer-required-skills').value = Array.isArray(job.required_skills) ? job.required_skills.join(', ') : '';
  document.getElementById('edit-offer-nice-skills').value = Array.isArray(job.nice_to_have_skills) ? job.nice_to_have_skills.join(', ') : '';

  form.onsubmit = async function(e) {
    e.preventDefault();
    await handleSaveOfferEdits(job);
    return false;
  };

  document.getElementById('cancel-edit-offer')?.addEventListener('click', (event) => {
    event.preventDefault();
    editingOfferId = null;
    renderOfferDetailsPanel(job);
  });
}

window.openApplicationCV = async function(applicationId) {
  if (!apiClient || typeof apiClient.openCV !== 'function') {
    showToast('La descarga de CV no está disponible todavía en el backend.', 'error');
    return;
  }

  try {
    await apiClient.openCV(applicationId);
  } catch (error) {
    console.error('Error opening CV:', error);
    if (error?.status === 404) {
      showToast('El endpoint de descarga o el CV no está disponible todavía.', 'error');
      return;
    }

    showToast(error.message || 'No se pudo abrir el CV', 'error');
  }
};

/**
 * Close offer status
 */
async function closeOfferStatus(job = null) {
  const targetJob = job || hrJobs.find(j => j.id === selectedJobId);
  if (!targetJob) return;

  const isClosed = targetJob.status === 'closed';
  const nextStatus = isClosed ? 'open' : 'closed';
  const actionTitle = isClosed ? 'Reabrir oferta' : 'Cerrar oferta';
  const confirmText = isClosed ? 'Reabrir oferta' : 'Cerrar oferta';
  const confirmMessage = isClosed
    ? '¿Seguro que deseas reabrir esta oferta? Los candidatos volverán a poder aplicar'
    : '¿Seguro que deseas cerrar esta oferta? Los candidatos no podrán aplicar';

  const confirmed = await showConfirmDialog(confirmMessage, {
    title: actionTitle,
    confirmText,
    cancelText: 'Cancelar',
  });

  if (!confirmed) {
    return;
  }
  
  try {
    UI.showLoading();
    const updatedOffer = isClosed
      ? await apiClient.updateJobOffer(targetJob.id, { status: 'open' })
      : await apiClient.closeJobOffer(targetJob.id);
    const mergedOffer = updatedOffer || { ...targetJob, status: nextStatus };

    hrJobs = hrJobs.map(item => item.id === targetJob.id ? { ...item, ...mergedOffer, status: nextStatus } : item);
    editingOfferId = null;

    renderMyOffers();
    renderOfferDetailsPanel(hrJobs.find(item => item.id === targetJob.id) || mergedOffer);
    UI.hideLoading();
    showToast(isClosed ? 'Oferta reabierta correctamente' : 'Oferta cerrada correctamente', 'success');
  } catch (error) {
    UI.hideLoading();
    console.error('Error closing offer:', error);
    showToast(error.message || 'No se pudo cerrar la oferta', 'error');
  }
}

async function handleSaveOfferEdits(job) {
  const titleInput = document.getElementById('edit-offer-title');
  const companyInput = document.getElementById('edit-offer-company');
  const locationInput = document.getElementById('edit-offer-location');
  const descriptionInput = document.getElementById('edit-offer-description');
  const employmentTypeSelect = document.getElementById('edit-offer-employment-type');
  const salaryMinInput = document.getElementById('edit-offer-salary-min');
  const salaryMaxInput = document.getElementById('edit-offer-salary-max');
  const requiredSkillsInput = document.getElementById('edit-offer-required-skills');
  const niceSkillsInput = document.getElementById('edit-offer-nice-skills');

  if (!titleInput.value.trim() || !companyInput.value.trim() || !locationInput.value.trim() || !descriptionInput.value.trim()) {
    showToast('Título, empresa, ubicación y descripción son requeridos', 'error');
    return;
  }

  try {
    UI.showLoading();

    const requiredSkills = requiredSkillsInput.value
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const niceSkills = niceSkillsInput.value
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

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
      status: job.status,
    };

    const updatedOffer = await apiClient.updateJobOffer(job.id, offerData);
    const mergedOffer = updatedOffer || { ...job, ...offerData };

    hrJobs = hrJobs.map(item => item.id === job.id ? { ...item, ...mergedOffer } : item);
    editingOfferId = null;

    renderMyOffers();
    renderOfferDetailsPanel(hrJobs.find(item => item.id === job.id) || mergedOffer);

    UI.hideLoading();
    showToast('¡Oferta de trabajo actualizada exitosamente!', 'success');
  } catch (error) {
    UI.hideLoading();
    console.error('Error updating offer:', error);
    showToast(error.message || 'Error al actualizar la oferta. Intenta de nuevo.', 'error');
  }
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
    showToast('Título, empresa, ubicación y descripción son requeridos', 'error');
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
    showToast('¡Oferta de trabajo creada exitosamente!', 'success');

    // Reset form
    document.getElementById('create-offer-form').reset();

    // Reload offers
    loadHRJobs();
  } catch (error) {
    UI.hideLoading();
    console.error('Error creating offer:', error);
    showToast(error.message || 'Error al crear la oferta. Intenta de nuevo.', 'error');
  }
}

/**
 * Load applications for a job
 */
async function loadApplicationsForJob(jobId) {
  try {
    UI.showLoading();

    const applicationsResponse = await apiClient.getApplicationsByJobOffer(jobId);
    const applications = Array.isArray(applicationsResponse) ? applicationsResponse : [];
    allApplications[jobId] = applications;
    console.log('Applications loaded:', applications);

    renderApplications(jobId);
    UI.hideLoading();
  } catch (error) {
    UI.hideLoading();
    console.error('Error loading applications:', error);
    showToast('Error al cargar las candidaturas. Intenta de nuevo.', 'error');
  }
}

/**
 * Render applications
 */
function renderApplications(jobId) {
  const container = document.getElementById('applications-list');
  const emptyState = document.getElementById('applications-empty');
  const applications = allApplications[jobId] || [];
  console.log('Applications loaded:', applications);

  if (applications.length === 0) {
    container.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';

  const html = `
    <div class="applications-list" style="display: grid; gap: 10px;">
      ${applications.map(app => `
        <article class="application-card" style="border: 1px solid var(--gray-200); border-radius: 8px; padding: 12px;">
          <h4 style="margin: 0 0 6px 0;">${app.candidate_name || '-'}</h4>
          <p style="margin: 2px 0;"><strong>Email:</strong> ${app.candidate_email || '-'}</p>
          <p style="margin: 2px 0;"><strong>CV:</strong> ${app.cv_original_filename || 'Sin CV'}</p>
          <p style="margin: 2px 0;"><strong>Tamaño:</strong> ${app.cv_size_bytes ? Format.fileSize(app.cv_size_bytes) : '-'}</p>
          <p style="margin: 2px 0;"><strong>Fecha:</strong> ${Format.dateTime(app.cv_uploaded_at || app.created_at)}</p>
          <p style="margin: 2px 0;"><strong>Estado:</strong> ${app.cv_processing_status || 'Pendiente'}</p>
          <div style="margin-top: 8px;">
            ${getCVActionHtml(app)}
          </div>
        </article>
      `).join('')}
    </div>
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

function getCVActionHtml(app) {
  if (!app?.cv_storage_key) {
    return '';
  }

  const storageKey = String(app.cv_storage_key).toLowerCase();
  const isLegacyLocalPath = storageKey.startsWith('storage/') || storageKey.startsWith('storage\\');

  if (isLegacyLocalPath) {
    return '<span class="badge badge--secondary">CV no disponible (test)</span>';
  }

  return `
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
      <button class="btn btn--secondary" onclick="openApplicationCV('${app.id}')">Abrir CV</button>
      <button class="btn btn--secondary" onclick="downloadApplicationCV('${app.id}')">Descargar</button>
    </div>
  `;
}

window.downloadApplicationCV = async function(applicationId) {
  if (!apiClient || typeof apiClient.downloadCV !== 'function') {
    showToast('La descarga de CV no está disponible todavía.', 'error');
    return;
  }

  try {
    await apiClient.downloadCV(applicationId);
  } catch (error) {
    console.error('Error downloading CV:', error);
    showToast(error.message || 'No se pudo descargar el CV', 'error');
  }
};

window.downloadAllCVs = async function(jobOfferId, jobOfferTitle) {
  if (!apiClient || typeof apiClient.downloadJobOfferCVs !== 'function') {
    showToast('La descarga masiva de CVs no está disponible todavía.', 'error');
    return;
  }

  try {
    await apiClient.downloadJobOfferCVs(jobOfferId, jobOfferTitle);
    showToast(`CVs descargados en la carpeta ${jobOfferTitle || 'oferta'}`, 'success');
  } catch (error) {
    console.error('Error downloading all CVs:', error);
    showToast(error.message || 'No se pudieron descargar los CVs', 'error');
  }
};
