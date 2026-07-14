/**
 * Apply Page Module
 * Handles job application form and CV upload
 */

let applicationJob = null;
let createdApplicationId = null;

/**
 * Initialize apply page
 */
window.initApply = async function(params) {
  if (params && params.job) {
    applicationJob = params.job;
  }

  if (!applicationJob) {
    showToast('Oferta no encontrada', 'error');
    router.navigate('home');
    return;
  }

  setupBackButton();

  const alreadyApplied = await hasAlreadyApplied(applicationJob.id);
  if (alreadyApplied) {
    renderAlreadyAppliedState();
    return;
  }

  setupApplyForm();
  populateUserData();
};

/**
 * Setup apply form
 */
function setupApplyForm() {
  const jobTitleEl = document.getElementById('apply-job-title');
  const form = document.getElementById('apply-form');
  const cvInput = document.getElementById('apply-cv');
  const cvNameEl = document.getElementById('apply-cv-name');

  jobTitleEl.textContent = applicationJob.title;

  // Handle file input change
  cvInput.onchange = function(e) {
    const file = e.target.files[0];
    if (file) {
      // Validate file
      if (!Validation.isValidPDF(file)) {
        showToast('El archivo debe ser un PDF válido', 'error');
        cvInput.value = '';
        cvNameEl.textContent = '';
        return;
      }

      if (!Validation.isValidFileSize(file)) {
        showToast('El archivo no puede superar 5 MB', 'error');
        cvInput.value = '';
        cvNameEl.textContent = '';
        return;
      }

      cvNameEl.textContent = `✓ ${file.name} (${Format.fileSize(file.size)})`;
    }
  };

  // Handle form submission
  form.onsubmit = async function(e) {
    e.preventDefault();
    await handleApplicationSubmit();
    return false;
  };
}

/**
 * Populate user data
 */
function populateUserData() {
  const user = authSystem.getCurrentUser();
  if (user) {
    const nameInput = document.getElementById('apply-name');
    const emailInput = document.getElementById('apply-email');
    const resolvedName = user.name || user.full_name || '';

    nameInput.value = resolvedName;
    emailInput.value = user.email || '';

    [nameInput, emailInput].forEach((input) => {
      input.readOnly = true;
      input.setAttribute('readonly', 'readonly');
      input.classList.add('form__input--readonly');
    });
  }
}

async function hasAlreadyApplied(jobOfferId) {
  const user = authSystem.getCurrentUser();
  if (!user?.email) {
    return false;
  }

  try {
    const applications = await apiClient.getApplicationsByJobOffer(jobOfferId);
    return applications.some((application) => {
      const candidateEmail = String(application.candidate_email || '').trim().toLowerCase();
      return candidateEmail && candidateEmail === String(user.email).trim().toLowerCase();
    });
  } catch (error) {
    console.error('Error checking existing application:', error);
    showToast('No se pudo comprobar si ya habías aplicado a esta oferta', 'info');
    return false;
  }
}

function renderAlreadyAppliedState() {
  const formCard = document.querySelector('#apply-page .form-card');
  if (!formCard) return;

  formCard.innerHTML = `
    <div class="empty-state" style="padding: var(--space-6) var(--space-4);">
      <div class="empty-state__icon">ℹ️</div>
      <h2 class="empty-state__title">Ya has aplicado a esta oferta</h2>
      <p class="empty-state__text">Puedes volver al listado para explorar otras oportunidades.</p>
      <a href="#" class="btn btn--primary" id="back-to-jobs-list">Volver al listado</a>
    </div>
  `;

  document.getElementById('back-to-jobs-list')?.addEventListener('click', (event) => {
    event.preventDefault();
    router.navigate('home');
  });
}

/**
 * Handle application submit
 */
async function handleApplicationSubmit() {
  const nameInput = document.getElementById('apply-name');
  const emailInput = document.getElementById('apply-email');
  const cvInput = document.getElementById('apply-cv');

  // Validate form
  if (!nameInput.value.trim()) {
    showToast('El nombre es requerido', 'error');
    return;
  }

  if (!emailInput.value.trim()) {
    showToast('El correo es requerido', 'error');
    return;
  }

  if (!cvInput.files[0]) {
    showToast('Debes adjuntar un CV', 'error');
    return;
  }

  try {
    UI.showLoading();

    // Step 1: Create application
    const application = await apiClient.createApplication(
      applicationJob.id,
      nameInput.value.trim(),
      emailInput.value.trim()
    );

    createdApplicationId = application.id;

    // Step 2: Upload CV
    const cvFile = cvInput.files[0];
    await apiClient.uploadCV(createdApplicationId, cvFile);

    UI.hideLoading();
    showToast('¡Tu candidatura ha sido enviada exitosamente!', 'success');

    // Reset form
    UI.clearForm('apply-form');
    document.getElementById('apply-cv-name').textContent = '';

    // Redirect after 2 seconds
    setTimeout(() => {
      router.navigate('home');
    }, 2000);
  } catch (error) {
    UI.hideLoading();
    console.error('Error submitting application:', error);
    
    const errorMessage = error.message || 'Error al enviar la candidatura. Por favor, intenta de nuevo.';
    showToast(errorMessage, 'error');
  }
}

/**
 * Setup back button
 */
function setupBackButton() {
  const backBtn = document.getElementById('back-from-apply');
  if (!backBtn) return;

  backBtn.onclick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    router.navigate('job-detail', { job: applicationJob });
    window.app?.updateNavLinks?.();
  };
}
