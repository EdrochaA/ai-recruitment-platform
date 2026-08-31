import requests
import json

# Test application ID and token from previous PowerShell session
app_id = "f5a07e2a-49c1-4fa8-890c-20dad043c63f"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNmExMmU0YTE3OWM3OTBiNzU0OWI5ZTA5IiwiZW1haWwiOiJjdnRlc3RAZ21haWwuY29tIiwicm9sZSI6ImNhbmRpZGF0ZSIsIm5hbWUiOiJDViBUZXN0IENhbmRpZGF0ZSIsImV4cCI6MTc3OTcwOTQ3MywiaWF0IjoxNzc5NjIzMDczfQ.2_8Yf1rZd_C6S35GLMS5XyjByHZCrl4Eh8bvk3HFFMA"
url = f"http://localhost:8000/applications/{app_id}/cv"

# Read the test PDF file
with open("test_cv.pdf", "rb") as f:
    file_content = f.read()

print(f"PDF file size: {len(file_content)} bytes")
print(f"URL: {url}")
print(f"Token length: {len(token)}")
print()

# Upload with proper multipart form-data
files = {"file": ("test_cv.pdf", file_content, "application/pdf")}
headers = {"Authorization": f"Bearer {token}"}

try:
    response = requests.post(url, files=files, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:")
    print(response.text)
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("Upload successful.")
        print(f"CV Original Filename: {result.get('cv_original_filename')}")
        print(f"CV Storage Key: {result.get('cv_storage_key')}")
        print(f"CV Size Bytes: {result.get('cv_size_bytes')}")
        print(f"CV Uploaded At: {result.get('cv_uploaded_at')}")
    else:
        print(f"Upload failed with status {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
