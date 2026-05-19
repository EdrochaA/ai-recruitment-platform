/**
 * Home Page Module
 * Displays list of job offers
 */

let currentJobs = [];
let filteredJobs = [];

/**
 * Initialize home page
 */
window.initHome = async function() {
  loadJobOffers();
  setupEventListeners();
  updateUIForAuthStatus();
};

/**
 * Load job offers from API
 */
async function loadJobOffers() {
  try {
    UI.showLoading();
    const jobs = await apiClient.getJobOffers();
    currentJobs = jobs || [];
    
    // Cache jobs
    Storage.saveJobCache(currentJobs);
    
    filteredJobs = [...currentJobs];
    renderJobListings();
    UI.hideLoading();
  } catch (error) {
    UI.hideLoading();
    console.error('Error loading jobs:', error);
    
    // Try to use cached data
    const cached = Storage.getJobCache();
    if (cached) {
      currentJobs = cached;
      filteredJobs = [...currentJobs];
      renderJobListings();
      UI.showError('Usando datos en caché. No se pudo conectar con el servidor.');
    } else {
      UI.showError('Error al cargar las ofertas de trabajo. Verifica la conexión con el servidor.');
    }
  }
}

/**
 * Render job listings
 */
function renderJobListings() {
  const container = document.getElementById('job-listings');
  const emptyState = document.getElementById('empty-state');

  if (filteredJobs.length === 0) {
    container.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';
  container.innerHTML = filteredJobs.map(job => createJobCard(job)).join('');

  // Add event listeners to cards
  container.querySelectorAll('.job-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (!e.target.classList.contains('btn')) {
        viewJobDetail(card.dataset.jobId);
      }
    });
  });

  // Add button event listeners
  container.querySelectorAll('[data-action="view"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      viewJobDetail(e.currentTarget.dataset.jobId);
    });
  });

  container.querySelectorAll('[data-action="apply"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      applyToJob(e.currentTarget.dataset.jobId);
    });
  });

  container.querySelectorAll('[data-action="login"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      router.showAuthModal();
    });
  });
}

/**
 * Create job card HTML
 */
function createJobCard(job) {
  const isAuthenticated = authSystem.isAuthenticated();
  const isCandidate = authSystem.isCandidate();

  let actionButtons = `
    <button class="btn btn--primary" data-action="view" data-job-id="${job.id}">
      Ver oferta
    </button>
  `;

  if (isAuthenticated && isCandidate) {
    actionButtons += `
      <button class="btn btn--secondary" data-action="apply" data-job-id="${job.id}">
        Aplicar
      </button>
    `;
  } else if (!isAuthenticated) {
    actionButtons += `
      <button class="btn btn--secondary" data-action="login">
        Iniciar sesión para aplicar
      </button>
    `;
  }

  return `
    <div class="job-card" data-job-id="${job.id}">
      <h3 class="job-card__title">${Format.truncate(job.title, 50)}</h3>
      <div class="job-card__location">
        📍 ${job.location}
      </div>
      <p class="job-card__description">${Format.truncate(job.description, 100)}</p>
      <div class="job-card__footer">
        <div class="job-card__meta">
          <span class="badge">${job.status || 'Abierta'}</span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          ${actionButtons}
        </div>
      </div>
    </div>
  `;
}

/**
 * View job detail
 */
function viewJobDetail(jobId) {
  const job = currentJobs.find(j => j.id === jobId);
  if (job) {
    router.navigate('job-detail', { job });
  }
}

/**
 * Apply to job
 */
function applyToJob(jobId) {
  const job = currentJobs.find(j => j.id === jobId);
  if (job) {
    router.navigate('apply', { job });
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  const searchInput = document.getElementById('search-input');
  
  if (searchInput) {
    searchInput.addEventListener('input', debounce(handleSearch, 300));
  }

  // Refresh button if exists
  const refreshBtn = document.querySelector('[data-action="refresh"]');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadJobOffers());
  }
}

/**
 * Handle search
 */
function handleSearch(e) {
  const query = e.target.value.toLowerCase();

  if (!query) {
    filteredJobs = [...currentJobs];
  } else {
    filteredJobs = currentJobs.filter(job =>
      job.title.toLowerCase().includes(query) ||
      job.location.toLowerCase().includes(query) ||
      job.description.toLowerCase().includes(query)
    );
  }

  renderJobListings();
}

/**
 * Update UI based on auth status
 */
function updateUIForAuthStatus() {
  // This is handled in the navbar update
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func.apply(this, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
