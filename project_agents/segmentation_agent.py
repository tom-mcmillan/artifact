"""Segmentation Agent.

This module segments input text into logical pieces.
"""

import re
import uuid
from typing import List, Dict
from utils.config import OPENAI_API_KEY
from agents.tool import function_tool
from agents.agent import Agent
from agents.model_settings import ModelSettings
from utils.models import Segment, SegmentationOutput

def segmentation_agent(input_text: str) -> List[Dict[str, str]]:
    """
    Segments the input_text into logical segments.

    Args:
        input_text (str): The text to segment.

    Returns:
        List of segments with 'id' and 'text'.
    """
    MIN_LEN = 250
    segments: List[Dict[str, str]] = []
    # split on empty lines (paragraphs)
    paras = re.split(r"\r?\n\s*\r?\n", input_text.strip())
    current: List[str] = []
    for para in paras:
        text = para.strip()
        if not text:
            continue
        if not current:
            # start new segment or emit long paragraph
            if len(text) >= MIN_LEN:
                seg_id = f"seg_{uuid.uuid4().hex}"
                segments.append({"id": seg_id, "text": text})
                continue
            current.append(text)
            continue
        # accumulate into current segment
        combined = "\n\n".join(current + [text])
        if len(combined) >= MIN_LEN:
            seg_id = f"seg_{uuid.uuid4().hex}"
            segments.append({"id": seg_id, "text": combined})
            current = []
        else:
            current.append(text)
    # handle leftover paragraphs
    if current:
        leftover = "\n\n".join(current)
        if len(leftover) >= MIN_LEN or not segments:
            seg_id = f"seg_{uuid.uuid4().hex}"
            segments.append({"id": seg_id, "text": leftover})
        else:
            segments[-1]["text"] += "\n\n" + leftover
    return segments

@function_tool
def segmentation_tool(text: str) -> SegmentationOutput:
    """
    Split the input text into segments of at least 250 characters, using paragraph logic.

    Returns a SegmentationOutput model.
    """
    segs = segmentation_agent(text)
    return SegmentationOutput(segments=[Segment(**s) for s in segs])

class SegmentationAgent(Agent):
    """
    Agent that segments raw session text into logical segments.
    """
    def __init__(self):
        super().__init__(
            name="SegmentationAgent",
            instructions=(
                "Use the segmentation_tool to split the input text into logical segments. "
                "Each segment must be at least 250 characters and represent a shift in epistemic focus or tension. "
                "Return JSON matching the SegmentationOutput schema."
            ),
            model="gpt-4o",
            model_settings=ModelSettings(temperature=0),
            tools=[segmentation_tool],
            output_type=SegmentationOutput,
            tool_use_behavior="stop_on_first_tool",
        )
        # No direct tool calls here; uses segmentation_tool
        
if __name__ == "__main__":
    sample_text = "Sample text to segment."
    print(segmentation_agent(sample_text))