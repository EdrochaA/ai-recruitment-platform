from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class JobApplication:
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
    cv_processing_status: Optional[str] = None  # pending, processed, failed
    cv_processed_at: Optional[datetime] = None
    cv_processing_error: Optional[str] = None

    # CV Analysis fields
    cv_analysis_status: str = "pending"  # pending, analyzing, completed, failed
    cv_analysis_score: Optional[int] = None  # 0-100
    cv_analysis_summary: Optional[str] = None
    cv_analysis_skills: Optional[list[str]] = None
    cv_analysis_experience: Optional[str] = None
    cv_analysis_candidate_name: Optional[str] = None
    cv_analysis_education: Optional[list[str]] = None
    cv_analysis_work_experience: Optional[list[str]] = None
    cv_analysis_technical_skills: Optional[list[str]] = None
    cv_analysis_soft_skills: Optional[list[str]] = None
    cv_analysis_languages: Optional[list[str]] = None
    cv_analysis_certifications: Optional[list[str]] = None
    cv_analysis_warnings: Optional[list[str]] = None
    cv_analyzed_at: Optional[datetime] = None
    cv_analysis_error: Optional[str] = None

    created_at: Optional[datetime] = None
