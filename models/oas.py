from pydantic import BaseModel
from typing import List, Optional


class ValidationReport(BaseModel):
    valid: bool
    errors: List[str]
    diff_html: Optional[str] = None
