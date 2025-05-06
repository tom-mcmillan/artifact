"""Artifact Assembler Agent.

This OpenAI Agent assembles validated segments into structured artifacts and saves them locally.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from agents.tool import function_tool
from agents.agent import Agent
from agents.model_settings import ModelSettings
from utils.models import EpistemicContourResult, EpistemicTrace, ArtifactOutput

@function_tool
def artifact_assembler_tool(segment_json: str) -> ArtifactOutput:
    """
    Convert a validated segment JSON into a final artifact.

    Generates a UUID-based artifact ID, timestamp, wraps content, and writes JSON file.
    """
    # Parse the input segment
    data = json.loads(segment_json)
    seg = EpistemicContourResult.parse_obj(data)
    if not seg.is_artifact:
        raise ValueError(f"Segment {seg.id} is not approved for artifacting.")

    # Build artifact
    art_id = f"know_{uuid4().hex}"
    created_at = datetime.utcnow().isoformat() + "Z"
    trace = EpistemicTrace(
        justification=seg.justification,
        diagnostic_flags=seg.diagnostic_flags,
        detected_by="EpistemicContourAgent"
    )
    artifact = ArtifactOutput(
        id=art_id,
        created_at=created_at,
        content=seg.text,
        epistemic_trace=trace
    )

    # Save to local file
    output_dir = Path("data/artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{art_id}.json"
    output_path.write_text(artifact.json(indent=2), encoding="utf-8")
    return artifact

class ArtifactAssemblerAgent(Agent):
    """
    Agent that wraps approved segments into final artifacts using a function tool.
    """
    def __init__(self):
        super().__init__(
            name="ArtifactAssemblerAgent",
            instructions=(
                "Use the artifact_assembler_tool to create a final artifact JSON from a validated segment. "
                "Save the artifact locally and return the JSON matching the ArtifactOutput schema."
            ),
            model="gpt-4o",
            model_settings=ModelSettings(temperature=0),
            tools=[artifact_assembler_tool],
            output_type=ArtifactOutput,
            tool_use_behavior="stop_on_first_tool",
        )