import importlib.util
import json
import sys
import types
import unittest

if importlib.util.find_spec("boto3") is None:
    boto3_module = types.ModuleType("boto3")
    boto3_module.client = lambda *args, **kwargs: None
    sys.modules["boto3"] = boto3_module

    botocore_module = types.ModuleType("botocore")
    botocore_config_module = types.ModuleType("botocore.config")
    botocore_exceptions_module = types.ModuleType("botocore.exceptions")
    botocore_config_module.Config = object
    botocore_exceptions_module.BotoCoreError = Exception
    botocore_exceptions_module.ClientError = Exception
    sys.modules["botocore"] = botocore_module
    sys.modules["botocore.config"] = botocore_config_module
    sys.modules["botocore.exceptions"] = botocore_exceptions_module

from app.adapters.agent.agentcore_candidate_ranker import AgentCoreCandidateRanker
from app.domain.ports.candidate_ranker import CandidateInput


class AgentCoreCandidateRankerTests(unittest.TestCase):
    def setUp(self):
        self.ranker = AgentCoreCandidateRanker(
            runtime_arn="arn:aws:bedrock-agentcore:eu-west-1:123:runtime/test",
            region="eu-west-1",
        )
        self.candidate = CandidateInput(
            application_id="valid-app",
            candidate_name="Ana",
            candidate_email="ana@example.com",
            cv_text="Python developer",
        )

    def test_prompt_excludes_candidates_without_cv_text_before_ranking(self):
        prompt = self.ranker._build_prompt("Backend Developer", 3)

        self.assertIn("cv_text contenga texto no vacío", prompt)
        self.assertIn("no deben consumir plazas del top", prompt)
        self.assertIn("min(3, evaluable_candidates)", prompt)

    def test_parser_skips_unknown_candidate_without_consuming_top_slot(self):
        response = json.dumps(
            {
                "total_candidates": 2,
                "evaluable_candidates": 1,
                "ranking": [
                    {
                        "application_id": "candidate-without-cv",
                        "candidate_name": "No evaluable",
                        "score": 99,
                        "reason": "Should be ignored",
                    },
                    {
                        "application_id": "valid-app",
                        "candidate_name": "Ana",
                        "score": 85,
                        "reason": "Buen ajuste",
                    },
                ],
                "summary": "Ranking completado.",
            }
        )

        ranked, summary = self.ranker._parse_response(response, [self.candidate], top_n=1)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].application_id, "valid-app")
        self.assertEqual(ranked[0].rank, 1)
        self.assertEqual(summary, "Ranking completado.")


if __name__ == "__main__":
    unittest.main()