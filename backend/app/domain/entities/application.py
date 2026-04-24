from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Application:
    id: str
    job_offer_id: str
    candidate_name: str
    candidate_email: str

    cv_original_filename: Optional[str] = None
    cv_storage_key: Optional[str] = None
    cv_content_type: Optional[str] = None
    cv_size_bytes: Optional[int] = None
    cv_uploaded_at: Optional[datetime] = None

    cv_text: Optional[str] = None
    created_at: datetime = None # type: ignore