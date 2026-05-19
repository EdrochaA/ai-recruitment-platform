/**
 * API Client Module
 * Handles all communication with the backend API
 */

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL || CONFIG.API_BASE_URL;
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

  async createJobOffer(title, location, description) {
    return this.request('/job-offers', {
      method: 'POST',
      body: JSON.stringify({
        title,
        location,
        description,
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
      const response = await fetch(`${this.baseURL}/applications/${applicationId}/cv`, {
        method: 'POST',
        body: formData,
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
