"""MongoDB implementation of JobApplicationRepository"""

import re
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from pymongo import MongoClient
from pymongo.database import Database

from app.domain.entities.job_application import JobApplication
from app.domain.ports.job_application_repository import JobApplicationRepository


class MongoDBJobApplicationRepository(JobApplicationRepository):
    """MongoDB adapter for job applications persistence"""

    def __init__(self, db: Database):
        self.db = db
        self.collection = db.get_collection("job_applications")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create necessary indexes"""
        self.collection.create_index("job_offer_id")
        self.collection.create_index([("job_offer_id", 1), ("candidate_email", 1)])
        self.collection.create_index("created_at")

    def save(self, job_application: JobApplication) -> JobApplication:
        """Save a new job application"""
        doc = self._job_application_to_doc(job_application)
        # Force the _id to be the string ID from the entity so it matches what was requested
        doc["_id"] = str(job_application.id)
        
        result = self.collection.insert_one(doc)

        return job_application

    def find_by_job_offer(self, job_offer_id: str) -> List[JobApplication]:
        """Find all applications for a job offer"""
        docs = list(self.collection.find({"job_offer_id": job_offer_id}))
        return [self._doc_to_job_application(doc) for doc in docs]

    def exists_by_job_offer_and_email(
        self,
        job_offer_id: str,
        candidate_email: str,
    ) -> bool:
        """Check whether an email has already applied to a job offer."""
        normalized_email = candidate_email.strip().lower()
        email_pattern = f"^{re.escape(normalized_email)}$"

        return self.collection.find_one(
            {
                "job_offer_id": job_offer_id,
                "candidate_email": {
                    "$regex": email_pattern,
                    "$options": "i",
                },
            },
            {"_id": 1},
        ) is not None

    def find_by_id(self, job_application_id: str) -> Optional[JobApplication]:
        """Find application by ID"""
        try:
            # Try ObjectId first
            obj_id = ObjectId(job_application_id)
            doc = self.collection.find_one({"_id": obj_id})
            if doc:
                return self._doc_to_job_application(doc)
        except Exception:
            # Fall back to string search
            doc = self.collection.find_one({"_id": job_application_id})
            if doc:
                return self._doc_to_job_application(doc)

        return None

    def update(self, job_application: JobApplication) -> JobApplication:
        """Update an existing job application"""
        doc = self._job_application_to_doc(job_application)
        
        try:
            # Try ObjectId first
            obj_id = ObjectId(job_application.id)
            result = self.collection.replace_one({"_id": obj_id}, doc)
            if result.matched_count > 0:
                return job_application
        except Exception:
            pass

        # Fall back to string id
        result = self.collection.replace_one({"_id": job_application.id}, doc)

        if result.matched_count == 0:
            raise ValueError("JobApplication not found")

        return job_application

    def _job_application_to_doc(self, job_application: JobApplication) -> dict:
        """Convert JobApplication entity to MongoDB document"""
        doc = {
            "job_offer_id": job_application.job_offer_id,
            "candidate_name": job_application.candidate_name,
            "candidate_email": job_application.candidate_email,
            "cv_original_filename": job_application.cv_original_filename,
            "cv_storage_key": job_application.cv_storage_key,
            "cv_content_type": job_application.cv_content_type,
            "cv_size_bytes": job_application.cv_size_bytes,
            "cv_uploaded_at": job_application.cv_uploaded_at,
            "cv_text": job_application.cv_text,
            "cv_processing_status": job_application.cv_processing_status,
            "cv_processed_at": job_application.cv_processed_at,
            "cv_processing_error": job_application.cv_processing_error,
            "cv_analysis_status": job_application.cv_analysis_status or "pending",
            "cv_analysis_score": job_application.cv_analysis_score,
            "cv_analysis_summary": job_application.cv_analysis_summary,
            "cv_analysis_skills": job_application.cv_analysis_skills,
            "cv_analysis_experience": job_application.cv_analysis_experience,
            "cv_analysis_candidate_name": job_application.cv_analysis_candidate_name,
            "cv_analysis_education": job_application.cv_analysis_education,
            "cv_analysis_work_experience": job_application.cv_analysis_work_experience,
            "cv_analysis_technical_skills": job_application.cv_analysis_technical_skills,
            "cv_analysis_soft_skills": job_application.cv_analysis_soft_skills,
            "cv_analysis_languages": job_application.cv_analysis_languages,
            "cv_analysis_certifications": job_application.cv_analysis_certifications,
            "cv_analysis_warnings": job_application.cv_analysis_warnings,
            "cv_analyzed_at": job_application.cv_analyzed_at,
            "cv_analysis_error": job_application.cv_analysis_error,
            "created_at": job_application.created_at,
        }

        # Add _id if present
        if job_application.id:
            try:
                doc["_id"] = ObjectId(job_application.id)
            except Exception:
                doc["_id"] = job_application.id

        return doc

    def _doc_to_job_application(self, doc: dict) -> JobApplication:
        """Convert MongoDB document to JobApplication entity"""
        return JobApplication(
            id=str(doc.get("_id", "")),
            job_offer_id=doc.get("job_offer_id", ""),
            candidate_name=doc.get("candidate_name", ""),
            candidate_email=doc.get("candidate_email", ""),
            cv_original_filename=doc.get("cv_original_filename"),
            cv_storage_key=doc.get("cv_storage_key"),
            cv_content_type=doc.get("cv_content_type"),
            cv_size_bytes=doc.get("cv_size_bytes"),
            cv_uploaded_at=doc.get("cv_uploaded_at"),
            cv_text=doc.get("cv_text"),
            cv_processing_status=doc.get("cv_processing_status"),
            cv_processed_at=doc.get("cv_processed_at"),
            cv_processing_error=doc.get("cv_processing_error"),
            cv_analysis_status=doc.get("cv_analysis_status", "pending"),
            cv_analysis_score=doc.get("cv_analysis_score"),
            cv_analysis_summary=doc.get("cv_analysis_summary"),
            cv_analysis_skills=doc.get("cv_analysis_skills"),
            cv_analysis_experience=doc.get("cv_analysis_experience"),
            cv_analysis_candidate_name=doc.get("cv_analysis_candidate_name"),
            cv_analysis_education=doc.get("cv_analysis_education"),
            cv_analysis_work_experience=doc.get("cv_analysis_work_experience"),
            cv_analysis_technical_skills=doc.get("cv_analysis_technical_skills"),
            cv_analysis_soft_skills=doc.get("cv_analysis_soft_skills"),
            cv_analysis_languages=doc.get("cv_analysis_languages"),
            cv_analysis_certifications=doc.get("cv_analysis_certifications"),
            cv_analysis_warnings=doc.get("cv_analysis_warnings"),
            cv_analyzed_at=doc.get("cv_analyzed_at"),
            cv_analysis_error=doc.get("cv_analysis_error"),
            created_at=doc.get("created_at"),
        )
