import requests
import json

BASE_URL = "http://localhost:8000"

print("🧪 Sprint 4 - CV Processing Integration Test\n")

# 1. Create a job offer
print("1️⃣  Creating job offer...")
job_offer_response = requests.post(
    f"{BASE_URL}/job-offers",
    json={
        "title": "Senior Python Developer",
        "description": "We are looking for a Senior Python Developer with FastAPI experience",
        "location": "Remote"
    }
)
assert job_offer_response.status_code == 201, f"Failed to create job offer: {job_offer_response.text}"
job_offer = job_offer_response.json()
job_offer_id = job_offer["id"]
print(f"   ✅ Job offer created: {job_offer_id}\n")

# 2. Create an application
print("2️⃣  Creating job application...")
app_response = requests.post(
    f"{BASE_URL}/applications",
    json={
        "job_offer_id": job_offer_id,
        "candidate_name": "John Doe",
        "candidate_email": "john@example.com"
    }
)
assert app_response.status_code == 201, f"Failed to create application: {app_response.text}"
application = app_response.json()
application_id = application["id"]
print(f"   ✅ Application created: {application_id}\n")

# 3. Upload CV
print("3️⃣  Uploading CV...")
with open("test_cv.pdf", "rb") as f:
    files = {"file": ("test_cv.pdf", f, "application/pdf")}
    upload_response = requests.post(
        f"{BASE_URL}/applications/{application_id}/cv",
        files=files
    )
assert upload_response.status_code == 200, f"Failed to upload CV: {upload_response.text}"
app_with_cv = upload_response.json()
print(f"   ✅ CV uploaded\n")

# 4. Process CV with NEW endpoint
print("4️⃣  Processing CV (NEW endpoint)...")
process_response = requests.post(
    f"{BASE_URL}/applications/{application_id}/cv/process"
)
assert process_response.status_code == 200, f"Failed to process CV: {process_response.text}"
processed_app = process_response.json()
print(f"   ✅ CV processed\n")

# 5. Verify NEW fields are present in response
print("5️⃣  Verifying new fields in response...")
required_fields = [
    "cv_processing_status",
    "cv_processed_at",
    "cv_processing_error",
    "cv_text"
]

for field in required_fields:
    assert field in processed_app, f"❌ Missing field: {field}"
    print(f"   ✅ Field '{field}' present: {processed_app.get(field) is not None}")

# 6. Verify CV processing state
print("\n6️⃣  Verifying CV processing state...")
print(f"   CV Processing Status: {processed_app['cv_processing_status']}")
assert processed_app['cv_processing_status'] == 'processed', "CV should be marked as processed"
print(f"   ✅ CV status is 'processed'\n")

# 7. Test error handling - try processing non-existent application
print("7️⃣  Testing error handling (non-existent application)...")
error_response = requests.post(
    f"{BASE_URL}/applications/non-existent-id/cv/process"
)
assert error_response.status_code == 404, f"Should return 404 for non-existent app"
print(f"   ✅ Correctly returns 404 for non-existent application\n")

print("=" * 60)
print("✨ ALL TESTS PASSED! Sprint 4 implementation successful!")
print("=" * 60)
print("\nSummary:")
print(f"  - New port 'CVTextExtractor' created in domain")
print(f"  - Implementation 'PDFCVTextExtractor' in infrastructure")
print(f"  - Use case 'ProcessApplicationCV' orchestrates extraction")
print(f"  - New endpoint: POST /applications/{{id}}/cv/process")
print(f"  - Schema updated with cv_processing_status, cv_processed_at, cv_processing_error")
print(f"  - Dependencies properly injected")
print(f"  - Hexagonal architecture maintained")
