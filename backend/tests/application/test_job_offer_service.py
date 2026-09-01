import unittest
from datetime import datetime

from app.application.services.job_offer_service import JobOfferService
from app.domain.entities.user import User, UserRole


class FakeJobOfferRepository:
    def __init__(self):
        self.offers = []

    async def create_job_offer(self, offer):
        offer.id = "offer-1"
        self.offers.append(offer)
        return offer


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    async def get_user_by_email(self, email):
        return self.user if self.user.email == email else None


class JobOfferServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_can_create_job_offer(self):
        admin = User(
            id="admin-1",
            name="Admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            created_at=datetime(2026, 1, 1),
        )
        offer_repository = FakeJobOfferRepository()
        service = JobOfferService(offer_repository, FakeUserRepository(admin))

        result = await service.create_job_offer(
            creator_email=admin.email,
            title="Backend Developer",
            company="Example Company",
            description="Python and FastAPI",
            location="Madrid",
            required_skills=["Python"],
        )

        self.assertEqual(result["id"], "offer-1")
        self.assertEqual(result["created_by"], admin.id)
        self.assertEqual(len(offer_repository.offers), 1)


if __name__ == "__main__":
    unittest.main()