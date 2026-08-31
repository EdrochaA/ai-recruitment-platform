import unittest
from types import SimpleNamespace

from app.application.use_cases.rank_candidates_for_offer import RankCandidatesForOffer
from app.domain.entities.job_application import JobApplication
from app.domain.ports.candidate_ranker import RankedCandidate


class FakeApplicationRepository:
    def __init__(self, applications):
        self.applications = applications

    def find_by_job_offer(self, job_offer_id):
        return self.applications

    def update(self, application):
        return application


class FakeRanker:
    def rank(self, **kwargs):
        candidate = kwargs["candidates"][0]
        return [
            RankedCandidate(
                rank=1,
                application_id=candidate.application_id,
                candidate_name=candidate.candidate_name,
                candidate_email=candidate.candidate_email,
                score=90,
                ranking_reason="Buen ajuste",
            )
        ], "Resumen del ranker."


class FailingExtractor:
    def extract_text(self, file_bytes, filename=None):
        raise ValueError("No extractable text")


class RankCandidatesForOfferTests(unittest.TestCase):
    def build_use_case(self, applications):
        offer = SimpleNamespace(
            id="offer-1",
            title="Backend Developer",
            description="Python y APIs",
            required_skills=["Python"],
        )
        offer_repository = SimpleNamespace(find_by_title=lambda title: offer)
        return RankCandidatesForOffer(
            job_offer_repository=offer_repository,
            application_repository=FakeApplicationRepository(applications),
            cv_text_extractor=FailingExtractor(),
            file_storage=SimpleNamespace(get=lambda key: b"pdf"),
            candidate_ranker=FakeRanker(),
        )

    def test_reports_total_and_excludes_candidates_without_usable_cv(self):
        applications = [
            JobApplication("app-1", "offer-1", "Ana", "ana@example.com"),
            JobApplication(
                "app-2",
                "offer-1",
                "Bruno",
                "bruno@example.com",
                cv_storage_key="cv-2",
                cv_text="Python developer",
            ),
            JobApplication(
                "app-3",
                "offer-1",
                "Carla",
                "carla@example.com",
                cv_storage_key="cv-3",
            ),
        ]

        result = self.build_use_case(applications).execute("Backend Developer", top_n=3)

        self.assertEqual(result["total_candidates"], 3)
        self.assertEqual(result["evaluable_candidates"], 1)
        self.assertEqual(result["candidates_without_cv"], 1)
        self.assertEqual(result["candidates_without_cv_text"], 1)
        self.assertEqual(len(result["ranked_candidates"]), 1)
        self.assertIn("**3 candidaturas**", result["message"])
        self.assertIn("**1 pudo evaluarse**", result["message"])
        self.assertIn("no tiene CV subido", result["message"])
        self.assertIn("CV no contiene texto extraíble", result["message"])

    def test_returns_empty_ranking_when_no_candidate_is_evaluable(self):
        applications = [
            JobApplication("app-1", "offer-1", "Ana", "ana@example.com"),
            JobApplication("app-2", "offer-1", "Bruno", "bruno@example.com"),
        ]

        result = self.build_use_case(applications).execute("Backend Developer", top_n=3)

        self.assertEqual(result["total_candidates"], 2)
        self.assertEqual(result["evaluable_candidates"], 0)
        self.assertEqual(result["ranked_candidates"], [])
        self.assertIn("Ninguna pudo evaluarse", result["message"])
        self.assertIn("No se ha generado ningún ranking", result["message"])


if __name__ == "__main__":
    unittest.main()