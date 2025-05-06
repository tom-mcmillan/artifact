"""Orchestration pipeline for artifacting sessions using OpenAI Agents SDK."""
#!/usr/bin/env python3
import asyncio
import json
import sys
import argparse
from pathlib import Path
# Ensure the project root is on sys.path, so project_agents can be imported when running script directly
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

# Load .env variables to ensure OPENAI_API_KEY is set early
from dotenv import load_dotenv
_dotenv_path = Path(__file__).parent.parent / ".env"
if _dotenv_path.exists():
    load_dotenv(dotenv_path=str(_dotenv_path))
else:
    print(f"Warning: .env file not found at {_dotenv_path}. Ensure OPENAI_API_KEY is set.")

from agents.run import Runner
from project_agents.segmentation_agent import segmentation_agent
from project_agents.epistemic_contour_agent import EpistemicContourAgent
from project_agents.artifact_assembler_agent import ArtifactAssemblerAgent

async def run_pipeline(session_filename: str, review: bool = False):
    """
    Execute the artifacting pipeline for a given session text file.
    """
    input_path = Path("data/input_sessions") / session_filename
    if not input_path.exists():
        print(f"Error: session file not found: {input_path}")
        return
    text = input_path.read_text(encoding="utf-8")
    print(f"Loaded session '{session_filename}' ({len(text)} chars)")

    # 1. Segmentation
    print("[*] Segmenting text...")
    segments = segmentation_agent(text)
    print(f"[+] Generated {len(segments)} segments.")

    # 2. Epistemic contour filtering
    contour_agent = EpistemicContourAgent()
    approved_segments = []
    for seg in segments:
        seg_id = seg["id"]
        print(f"[*] Analyzing segment {seg_id}...")
        result = await Runner.run(contour_agent, json.dumps(seg, ensure_ascii=False))
        # Runner.run returns a RunResult; final_output holds the parsed output object
        output = result.final_output
        for seg_res in output.segments:
            if seg_res.is_artifact:
                print(f"[+] Segment {seg_res.id} approved for artifacting.")
                if review:
                    # Show snippet for human review
                    lines = seg_res.text.splitlines()
                    preview = "\n".join(lines[:3])
                    print("--- Segment Preview (first 3 lines) ---")
                    print(preview)
                    print("--- End Preview ---")
                    print(f"Diagnostic flags: {seg_res.diagnostic_flags}")
                    print(f"Justification: {seg_res.justification}\n")
                    choice = input("Accept this as an artifact? (Y/n): ").strip().lower()
                    if choice == 'n':
                        print(f"[-] User rejected segment {seg_res.id}.")
                        continue
                approved_segments.append(seg_res)
            else:
                print(f"[-] Segment {seg_res.id} rejected.")

    # 3. Artifact assembly
    assembler_agent = ArtifactAssemblerAgent()
    for seg_res in approved_segments:
        print(f"[*] Assembling artifact for segment {seg_res.id}...")
        art_result = await Runner.run(assembler_agent, json.dumps(seg_res.model_dump(), ensure_ascii=False))
        # Use final_output for the resulting ArtifactOutput
        artifact = art_result.final_output
        print(f"[+] Artifact '{artifact.id}' created.")

    print("Pipeline completed.")

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate the artifacting pipeline for a session text file."
    )
    parser.add_argument(
        'session_filename',
        help='Session .txt filename in data/input_sessions/'
    )
    parser.add_argument(
        '--review',
        action='store_true',
        help='Enable human-in-the-loop review of approved segments.'
    )
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.session_filename, review=args.review))

if __name__ == "__main__":
    main()