/**
 * Admin Dashboard Module
 * Allows admin users to manage HR users
 */

/**
 * Initialize admin dashboard
 */
window.initAdminDashboard = async function() {
  setupCreateHRForm();
  setupManageOffersButton();
  await loadHRUsers();
};

function setupManageOffersButton() {
  const button = document.getElementById('admin-manage-offers');
  if (button) {
    button.onclick = () => router.navigate('hr-dashboard');
  }
}

/**
 * Setup create HR form
 */
function setupCreateHRForm() {
  const form = document.getElementById('create-hr-form');
  if (form) {
    const passwordInput = document.getElementById('hr-password');
    if (passwordInput) {
      passwordInput.setAttribute('autocomplete', 'new-password');
    }

    form.onsubmit = async function(e) {
      e.preventDefault();
      await handleCreateHRUser();
      return false;
    };
  }
}

/**
 * Handle create HR user
 */
async function handleCreateHRUser() {
  const nameInput = document.getElementById('hr-name');
  const emailInput = document.getElementById('hr-email');
  const passwordInput = document.getElementById('hr-password');

  // Validate
  if (!nameInput.value.trim()) {
    showToast('El nombre es requerido', 'error');
    return;
  }

  if (!emailInput.value.trim() || !Validation.isValidEmail(emailInput.value)) {
    showToast('El correo debe ser válido', 'error');
    return;
  }

  if (!passwordInput.value || !Validation.isValidPassword(passwordInput.value)) {
    showToast('La contraseña debe tener entre 8 caracteres y 72 bytes, una letra y un carácter especial', 'error');
    return;
  }

  try {
    const result = await authSystem.createHRUser(
      nameInput.value.trim(),
      emailInput.value.trim(),
      passwordInput.value
    );

    if (!result.success) {
      showToast(result.error, 'error');
      return;
    }

    showToast('Usuario HR creado exitosamente', 'success');

    // Reset form
    document.getElementById('create-hr-form')?.reset();

    // Reload users list
    await loadHRUsers();
  } catch (error) {
    console.error('Error creating HR user:', error);
    showToast('Error al crear el usuario. Intenta de nuevo.', 'error');
  }
}

/**
 * Load HR users
 */
async function loadHRUsers() {
  try {
    const users = await authSystem.getHRUsers();
    renderHRUsers(users);
  } catch (error) {
    console.error('Error loading HR users:', error);
    renderHRUsers([]);
    showToast('No se pudieron cargar los usuarios de Recursos Humanos', 'error');
  }
}

/**
 * Render HR users table
 */
function renderHRUsers(users) {
  const container = document.getElementById('hr-users-list');

  if (users.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No hay usuarios HR registrados</p>';
    return;
  }

  const html = `
    <table class="table">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Correo</th>
          <th>Creado</th>
        </tr>
      </thead>
      <tbody>
        ${users.map(user => `
          <tr>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${Format.date(user.created_at)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}
