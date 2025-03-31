from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Note:
    id: int
    customer: str
    timestamp: str
    tags: Optional[str]  # Stored as comma-separated string
    notes: str
    items: Optional[List[dict]]  # List of {"text": str, "status": str}
    deadlines: Optional[List[str]]
    archived: bool = False