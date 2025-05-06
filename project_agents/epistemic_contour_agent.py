"""Epistemic Contour Agent.

This OpenAI Agent analyzes whether text segments are epistemically whole knowledge artifacts.
"""

from agents.agent import Agent
from agents.agent_output import AgentOutputSchema
from agents.model_settings import ModelSettings
from utils.models import EpistemicContourOutput

class EpistemicContourAgent(Agent):
    """
    Determines if segments are coherent, meaningful, and reusable artifacts.

    Criteria:
    - Coherence: the text must form a self-contained, understandable idea.
    - Independently meaningful: can stand alone as a referable thought.
    - Contains a conceptual decision, turn, or model.
    - Avoid overfitting: focus on epistemic integrity.
    """
    def __init__(self):
        super().__init__(
            name="EpistemicContourAgent",
            instructions=(
                "You are an Epistemic Contour Agent. You receive a single segment as a JSON object "
                "with 'id' and 'text'. Assess if it is a self-contained knowledge artifact. "
                "Use these criteria: coherence, independent meaningfulness, reusability, and presence of a conceptual decision or model. "
                "Return valid JSON matching the EpistemicContourOutput schema."
            ),
            # Use a model that supports JSON schema directives
            model="gpt-4o",
            model_settings=ModelSettings(temperature=0),
            # Enable strict JSON schema enforcement
            output_type=AgentOutputSchema(EpistemicContourOutput),
        )

if __name__ == "__main__":
    # Example usage
    agent = EpistemicContourAgent()
    sample = {"id": "seg1", "text": "Example segment text."}
    import asyncio, json
    print(asyncio.run(agent.run(json.dumps(sample, ensure_ascii=False))))