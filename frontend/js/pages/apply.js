/**
 * Apply Page Module
 * Handles job application form and CV upload
 */

let applicationJob = null;
let createdApplicationId = null;

/**
 * Initialize apply page
 */
window.initApply = function(params) {
  if (params && params.job) {
    applicationJob = params.job;
  }

  if (!applicationJob) {
    UI.showError('Oferta no encontrada');
    router.navigate('home');
    return;
  }

  setupApplyForm();
  setupBackButton();
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
        UI.showError('El archivo debe ser un PDF válido');
        cvInput.value = '';
        cvNameEl.textContent = '';
        return;
      }

      if (!Validation.isValidFileSize(file)) {
        UI.showError('El archivo no puede superar 5 MB');
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
    document.getElementById('apply-name').value = user.name || '';
    document.getElementById('apply-email').value = user.email || '';
  }
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
    UI.showError('El nombre es requerido');
    return;
  }

  if (!emailInput.value.trim()) {
    UI.showError('El correo es requerido');
    return;
  }

  if (!cvInput.files[0]) {
    UI.showError('Debes adjuntar un CV');
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
    UI.showSuccess('¡Tu candidatura ha sido enviada exitosamente!');

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
    UI.showError(errorMessage);
  }
}

/**
 * Setup back button
 */
function setupBackButton() {
  const backBtn = document.getElementById('back-from-apply');
  if (backBtn) {
    backBtn.onclick = function(e) {
      e.preventDefault();
      router.navigate('job-detail', { job: applicationJob });
      return false;
    };
  }
}
