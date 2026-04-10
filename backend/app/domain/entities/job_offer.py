from dataclasses import dataclass
from datetime import datetime


@dataclass
class JobOffer:
    id: str
    title: str
    description: str
    location: str
    status: str
    created_at: datetime