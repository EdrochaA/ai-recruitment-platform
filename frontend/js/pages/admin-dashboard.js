/**
 * Admin Dashboard Module
 * Allows admin users to manage HR users
 */

/**
 * Initialize admin dashboard
 */
window.initAdminDashboard = function() {
  setupCreateHRForm();
  loadHRUsers();
};

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
    showToast('La contraseña debe tener al menos 6 caracteres', 'error');
    return;
  }

  try {
    const result = authSystem.createHRUser(
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
    form.reset();

    // Reload users list
    loadHRUsers();
  } catch (error) {
    console.error('Error creating HR user:', error);
    showToast('Error al crear el usuario. Intenta de nuevo.', 'error');
  }
}

/**
 * Load HR users
 */
function loadHRUsers() {
  const users = authSystem.getHRUsers();
  renderHRUsers(users);
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
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        ${users.map(user => `
          <tr>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${Format.date(user.createdAt)}</td>
            <td>
              <button class="btn btn--ghost" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" data-action="reset-password" data-email="${user.email}">
                Reset
              </button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.innerHTML = html;

  // Add event listeners
  container.querySelectorAll('[data-action="reset-password"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const email = e.currentTarget.dataset.email;
      handleResetPassword(email);
    });
  });
}

/**
 * Handle reset password
 */
function handleResetPassword(email) {
  const newPassword = prompt(`Ingresa la nueva contraseña para ${email}:`);
  
  if (!newPassword) {
    return;
  }

  if (!Validation.isValidPassword(newPassword)) {
    showToast('La contraseña debe tener al menos 6 caracteres', 'error');
    return;
  }

  try {
    const users = authSystem.getAllUsers();
    if (users[email]) {
      users[email].password = newPassword;
      localStorage.setItem(authSystem.USERS_KEY, JSON.stringify(users));
      showToast('Contraseña actualizada exitosamente', 'success');
      loadHRUsers();
    }
  } catch (error) {
    console.error('Error resetting password:', error);
    showToast('Error al actualizar la contraseña', 'error');
  }
}
