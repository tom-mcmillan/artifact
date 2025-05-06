"""Pydantic models for artifacting pipeline."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Segment(BaseModel):
    id: str
    text: str

class SegmentationOutput(BaseModel):
    segments: List[Segment]

class EpistemicContourResult(BaseModel):
    id: str
    text: str
    is_artifact: bool = Field(..., description="Whether this segment is an artifact")
    justification: str = Field(..., description="Justification for the artifact decision")
    diagnostic_flags: List[str] = Field(default_factory=list, description="Diagnostic flags for issues or uncertainties")

class EpistemicContourOutput(BaseModel):
    segments: List[EpistemicContourResult]

class Artifact(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class EpistemicTrace(BaseModel):
    """Trace information for artifact provenance."""
    justification: str
    diagnostic_flags: List[str]
    detected_by: str
    
class ArtifactOutput(BaseModel):
    """Final artifact structure produced by ArtifactAssemblerAgent."""
    id: str
    created_at: str
    content: str
    epistemic_trace: EpistemicTrace