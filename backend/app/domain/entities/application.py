from dataclasses import dataclass
from datetime import datetime


@dataclass
class Application:
    id: str
    job_offer_id: str
    candidate_name: str
    candidate_email: str
    cv_text: str
    created_at: datetime