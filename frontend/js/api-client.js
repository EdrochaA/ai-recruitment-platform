/**
 * API Client Module
 * Handles all communication with the backend API
 */

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL || CONFIG.API_BASE_URL;
  }

  /**
   * Get auth token from localStorage
   */
  getAuthToken() {
    try {
      const session = localStorage.getItem('ai_recruitment_auth');
      if (session) {
        const data = JSON.parse(session);
        return data.access_token;
      }
    } catch (error) {
      console.error('Error reading auth token:', error);
    }
    return null;
  }

  /**
   * Generic fetch wrapper
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    const token = this.getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        timeout: CONFIG.TIMEOUT,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          status: response.status,
          message: errorData.detail || 'Error en la solicitud',
          data: errorData,
        };
      }

      return await response.json();
    } catch (error) {
      console.error('[API Error]', endpoint, error);
      throw error;
    }
  }

  /**
   * Job Offers API
   */

  async getJobOffers() {
    return this.request('/job-offers');
  }

  async createJobOffer(offerData) {
    // Validate user has auth token and proper role
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Debes iniciar sesión para crear ofertas');
    }

    // Parse token to check role
    try {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));
      if (!['admin', 'hr'].includes(payload.role)) {
        throw new Error('Solo administradores y RRHH pueden crear ofertas');
      }
    } catch (error) {
      if (error.message.includes('Solo')) throw error;
      console.warn('Could not verify role from token, will rely on backend validation');
    }

    return this.request('/job-offers', {
      method: 'POST',
      body: JSON.stringify({
        title: offerData.title,
        company: offerData.company,
        location: offerData.location,
        description: offerData.description,
        employment_type: offerData.employment_type || 'full-time',
        salary_min: offerData.salary_min || 0,
        salary_max: offerData.salary_max || 0,
        currency: 'EUR',
        required_skills: offerData.required_skills || [],
        nice_to_have_skills: offerData.nice_to_have_skills || [],
      }),
    });
  }

  /**
   * Applications API
   */

  async createApplication(jobOfferId, candidateName, candidateEmail) {
    return this.request('/applications', {
      method: 'POST',
      body: JSON.stringify({
        job_offer_id: jobOfferId,
        candidate_name: candidateName,
        candidate_email: candidateEmail,
      }),
    });
  }

  async getApplicationsByJobOffer(jobOfferId) {
    return this.request(`/applications/job-offer/${jobOfferId}`);
  }

  async uploadCV(applicationId, file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const headers = {};
      const token = this.getAuthToken();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/applications/${applicationId}/cv`, {
        method: 'POST',
        body: formData,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          status: response.status,
          message: errorData.detail || 'Error al subir el CV',
          data: errorData,
        };
      }

      return await response.json();
    } catch (error) {
      console.error('[API Error] Upload CV', error);
      throw error;
    }
  }

  getCVDownloadUrl(applicationId) {
    return `${this.baseURL}/applications/${applicationId}/cv/download`;
  }

  async openCV(applicationId) {
    const url = this.getCVDownloadUrl(applicationId);
    const headers = {};
    const token = this.getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, { headers });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        status: response.status,
        message: errorData.detail || 'No se pudo abrir el CV',
        data: errorData,
      };
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const newWindow = window.open(objectUrl, '_blank', 'noopener,noreferrer');
    if (!newWindow) {
      URL.revokeObjectURL(objectUrl);
      throw new Error('El navegador bloqueó la apertura del CV');
    }

    setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      return await this.request('/');
    } catch (error) {
      return { ok: false, error };
    }
  }

  /**
   * Set new base URL
   */
  setBaseURL(url) {
    this.baseURL = url;
    localStorage.setItem('apiBaseUrl', url);
  }
}

// Export singleton instance
const apiClient = new APIClient();
window.apiClient = apiClient;
