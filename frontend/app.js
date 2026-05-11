const statusEl = document.getElementById("status");
const baseUrlInput = document.getElementById("baseUrl");
const saveBaseUrlBtn = document.getElementById("saveBaseUrl");
const offersList = document.getElementById("offersList");
const applicationsList = document.getElementById("applicationsList");
const analysisResult = document.getElementById("analysisResult");

const offerIdFilter = document.getElementById("offerIdFilter");
const applicationIdInput = document.getElementById("applicationId");
const cvFileInput = document.getElementById("cvFile");

const baseUrlKey = "aiRecruitmentBaseUrl";

function setStatus(message, tone = "info") {
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
}

function getBaseUrl() {
  return baseUrlInput.value.trim();
}

function saveBaseUrl() {
  const url = getBaseUrl();
  if (!url) {
    setStatus("Base URL required", "error");
    return;
  }
  localStorage.setItem(baseUrlKey, url);
  setStatus("Base URL saved", "success");
}

async function apiRequest(path, options = {}) {
  const url = `${getBaseUrl()}${path}`;
  setStatus(`Calling ${path}...`, "info");
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch (err) {
      // ignore
    }
    throw new Error(detail);
  }
  const data = await response.json();
  setStatus("Success", "success");
  return data;
}

function renderOffers(offers) {
  offersList.innerHTML = "";
  offers.forEach((offer) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>${offer.title}</h3>
      <div class="badge">${offer.id}</div>
      <div>${offer.location}</div>
      <div>${offer.description}</div>
    `;
    card.addEventListener("click", () => {
      offerIdFilter.value = offer.id;
      document.querySelector("#createApplicationForm input[name='job_offer_id']").value = offer.id;
    });
    offersList.appendChild(card);
  });
}

function renderApplications(apps) {
  applicationsList.innerHTML = "";
  apps.forEach((app) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>${app.candidate_name}</h3>
      <div class="badge">${app.id}</div>
      <div>${app.candidate_email}</div>
      <div>CV status: ${app.cv_processing_status || "not processed"}</div>
      <div>Analysis status: ${app.cv_analysis_status || "pending"}</div>
    `;
    card.addEventListener("click", () => {
      applicationIdInput.value = app.id;
      showAnalysis(app);
    });
    applicationsList.appendChild(card);
  });
}

function showAnalysis(app) {
  const summary = {
    score: app.cv_analysis_score,
    summary: app.cv_analysis_summary,
    skills: app.cv_analysis_skills,
    experience: app.cv_analysis_experience,
    status: app.cv_analysis_status,
    error: app.cv_analysis_error,
  };
  analysisResult.textContent = JSON.stringify(summary, null, 2);
}

async function refreshOffers() {
  try {
    const offers = await apiRequest("/job-offers");
    renderOffers(offers);
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function createOffer(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    title: form.title.value,
    description: form.description.value,
    location: form.location.value,
  };

  try {
    await apiRequest("/job-offers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    form.reset();
    refreshOffers();
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function listApplications() {
  const offerId = offerIdFilter.value.trim();
  if (!offerId) {
    setStatus("Job offer id required", "error");
    return;
  }

  try {
    const apps = await apiRequest(`/applications/job-offer/${offerId}`);
    renderApplications(apps);
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function createApplication(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    job_offer_id: form.job_offer_id.value,
    candidate_name: form.candidate_name.value,
    candidate_email: form.candidate_email.value,
  };

  try {
    const app = await apiRequest("/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applicationIdInput.value = app.id;
    form.reset();
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function uploadCv() {
  const applicationId = applicationIdInput.value.trim();
  const file = cvFileInput.files[0];
  if (!applicationId || !file) {
    setStatus("Application id and PDF required", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const app = await apiRequest(`/applications/${applicationId}/cv`, {
      method: "POST",
      body: formData,
    });
    showAnalysis(app);
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function processCv() {
  const applicationId = applicationIdInput.value.trim();
  if (!applicationId) {
    setStatus("Application id required", "error");
    return;
  }

  try {
    const app = await apiRequest(`/applications/${applicationId}/cv/process`, {
      method: "POST",
    });
    showAnalysis(app);
  } catch (err) {
    setStatus(err.message, "error");
  }
}

async function analyzeCv() {
  const applicationId = applicationIdInput.value.trim();
  if (!applicationId) {
    setStatus("Application id required", "error");
    return;
  }

  try {
    const app = await apiRequest(`/applications/${applicationId}/cv/analyze`, {
      method: "POST",
    });
    showAnalysis(app);
  } catch (err) {
    setStatus(err.message, "error");
  }
}

function loadBaseUrl() {
  const saved = localStorage.getItem(baseUrlKey);
  baseUrlInput.value = saved || "http://localhost:8000";
}

saveBaseUrlBtn.addEventListener("click", saveBaseUrl);
document.getElementById("refreshOffers").addEventListener("click", refreshOffers);
document.getElementById("createOfferForm").addEventListener("submit", createOffer);
document.getElementById("listApplications").addEventListener("click", listApplications);
document.getElementById("createApplicationForm").addEventListener("submit", createApplication);
document.getElementById("uploadCv").addEventListener("click", uploadCv);
document.getElementById("processCv").addEventListener("click", processCv);
document.getElementById("analyzeCv").addEventListener("click", analyzeCv);

loadBaseUrl();
refreshOffers();
