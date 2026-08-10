from pydantic import BaseModel
from typing import Dict, List, Tuple


class ParameterResult(BaseModel):
    detected_rgb: Tuple[int, int, int]
    result: str
    matched_reference_rgb: Tuple[int, int, int]
    distance: float


class AnalysisResponse(BaseModel):
    filename: str
    results: Dict[str, ParameterResult]