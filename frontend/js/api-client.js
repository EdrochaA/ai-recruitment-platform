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

  async createJobOffer(title, location, description, company = '') {
    return this.request('/job-offers', {
      method: 'POST',
      body: JSON.stringify({
        title,
        location,
        description,
        company: company || 'Your Company',
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
