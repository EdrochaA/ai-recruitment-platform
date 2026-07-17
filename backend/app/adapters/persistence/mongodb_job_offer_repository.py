"""
MongoDB JobOffer Repository Adapter
Implementation of JobOfferRepositoryPort using MongoDB
"""

import logging
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)

from app.domain.entities.job_offer import JobOffer, JobOfferStatus
from app.domain.ports.job_offer_repository_port import JobOfferRepositoryPort


class MongoDBJobOfferRepository(JobOfferRepositoryPort):
    """MongoDB implementation of job offer repository"""
    
    def __init__(self, connection_string: str, database_name: str):
        """Initialize MongoDB connection"""
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.offers_collection = self.db["job_offers"]
        
        # Create indexes
        self.offers_collection.create_index("status")
        self.offers_collection.create_index("created_by")
    
    async def create_job_offer(self, job_offer: JobOffer) -> JobOffer:
        """Create a new job offer in MongoDB"""
        offer_doc = {
            "title": job_offer.title,
            "company": job_offer.company,
            "description": job_offer.description,
            "location": job_offer.location,
            "created_by": job_offer.created_by,
            "created_at": job_offer.created_at,
            "status": job_offer.status.value,
            "salary_min": job_offer.salary_min,
            "salary_max": job_offer.salary_max,
            "currency": job_offer.currency,
            "employment_type": job_offer.employment_type,
            "required_skills": job_offer.required_skills,
            "nice_to_have_skills": job_offer.nice_to_have_skills,
        }
        
        result = self.offers_collection.insert_one(offer_doc)
        job_offer.id = str(result.inserted_id)
        return job_offer
    
    async def get_job_offer(self, offer_id: str) -> Optional[JobOffer]:
        """Get job offer by ID from MongoDB"""
        try:
            offer_doc = self.offers_collection.find_one({"_id": ObjectId(offer_id)})
            if not offer_doc:
                return None
            return self._doc_to_job_offer(offer_doc)
        except InvalidId:
            return None
        except Exception:
            logger.exception("Unexpected error fetching job offer id=%s", offer_id)
            return None
    
    async def list_open_offers(self) -> List[JobOffer]:
        """List all open job offers"""
        offers = []
        for offer_doc in self.offers_collection.find({"status": JobOfferStatus.OPEN.value}):
            offers.append(self._doc_to_job_offer(offer_doc))
        return offers
    
    async def list_offers_by_creator(self, creator_id: str) -> List[JobOffer]:
        """List job offers created by a specific HR/Admin"""
        offers = []
        for offer_doc in self.offers_collection.find({"created_by": creator_id}):
            offers.append(self._doc_to_job_offer(offer_doc))
        return offers
    
    async def update_job_offer(self, offer_id: str, job_offer: JobOffer) -> Optional[JobOffer]:
        """Update a job offer"""
        try:
            update_doc = {
                "title": job_offer.title,
                "company": job_offer.company,
                "description": job_offer.description,
                "location": job_offer.location,
                "status": job_offer.status.value,
                "salary_min": job_offer.salary_min,
                "salary_max": job_offer.salary_max,
                "currency": job_offer.currency,
                "employment_type": job_offer.employment_type,
                "required_skills": job_offer.required_skills,
                "nice_to_have_skills": job_offer.nice_to_have_skills,
            }
            
            result = self.offers_collection.update_one(
                {"_id": ObjectId(offer_id)},
                {"$set": update_doc}
            )
            
            if result.matched_count == 0:
                return None
            
            updated_doc = self.offers_collection.find_one({"_id": ObjectId(offer_id)})
            return self._doc_to_job_offer(updated_doc)
        except InvalidId:
            return None
        except Exception:
            logger.exception("Unexpected error updating job offer id=%s", offer_id)
            return None
    
    async def delete_job_offer(self, offer_id: str) -> bool:
        """Delete a job offer"""
        try:
            result = self.offers_collection.delete_one({"_id": ObjectId(offer_id)})
            return result.deleted_count > 0
        except InvalidId:
            return False
        except Exception:
            logger.exception("Unexpected error deleting job offer id=%s", offer_id)
            return False
    
    def _doc_to_job_offer(self, doc: dict) -> JobOffer:
        """Convert MongoDB document to JobOffer domain model"""
        return JobOffer(
            id=str(doc["_id"]),
            title=doc["title"],
            company=doc["company"],
            description=doc["description"],
            location=doc["location"],
            created_by=doc["created_by"],
            created_at=doc["created_at"],
            status=JobOfferStatus(doc.get("status", "open")),
            salary_min=doc.get("salary_min", 0.0),
            salary_max=doc.get("salary_max", 0.0),
            currency=doc.get("currency", "EUR"),
            employment_type=doc.get("employment_type", "full-time"),
            required_skills=doc.get("required_skills", []),
            nice_to_have_skills=doc.get("nice_to_have_skills", []),
        )
    
    # ── Sync helpers used by rank-candidates use case ─────────────────────

    def list_all(self) -> list:
        """Return all job offers (synchronous)."""
        return [
            self._doc_to_job_offer(doc)
            for doc in self.offers_collection.find({})
        ]

    def find_by_title(self, title: str):
        """Find a job offer by partial, case-insensitive title match (synchronous)."""
        import re as _re

        title_escaped = _re.escape(title.strip())

        try:
            # Exact match first
            doc = self.offers_collection.find_one(
                {"title": {"$regex": f"^{title_escaped}$", "$options": "i"}}
            )
            if doc:
                return self._doc_to_job_offer(doc)

            # Partial match (title searched for is contained in offer title)
            doc = self.offers_collection.find_one(
                {"title": {"$regex": title_escaped, "$options": "i"}}
            )
            if doc:
                return self._doc_to_job_offer(doc)

            return None
        except Exception:
            logger.exception("Unexpected error in find_by_title(title=%r)", title)
            raise

    def find_by_id(self, offer_id: str) -> Optional["JobOffer"]:
        """Find a job offer by its ObjectId (synchronous).

        Returns None for an invalid/unknown ObjectId (treat as 404).
        Re-raises any infrastructure error (connection, timeout, etc.) so
        callers can surface it as a 500 rather than a silent empty result.
        """
        try:
            doc = self.offers_collection.find_one({"_id": ObjectId(offer_id)})
            if not doc:
                return None
            return self._doc_to_job_offer(doc)
        except InvalidId:
            logger.warning("find_by_id called with invalid ObjectId %r", offer_id)
            return None
        except Exception:
            logger.exception("Unexpected error in find_by_id(offer_id=%r)", offer_id)
            raise

    def close(self):
        """Close MongoDB connection"""
        self.client.close()
