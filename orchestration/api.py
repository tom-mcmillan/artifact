import json

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import uvicorn

from utils.db_client import DBClient
from project_agents.segmentation_agent import segmentation_agent
from project_agents.epistemic_contour_agent import EpistemicContourAgent
from project_agents.artifact_assembler_agent import ArtifactAssemblerAgent
from agents.run import Runner


async def ingest(request: Request):
    """
    Ingest endpoint: receives user_id, thread_id, and turns[] JSON.
    Runs artifacting pipeline and inserts artifacts into the database.
    Returns list of knowledge_ids.
    """
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON payload"}, status_code=400)

    user_id = payload.get("user_id")
    thread_id = payload.get("thread_id")
    turns = payload.get("turns")
    if user_id is None or thread_id is None or turns is None:
        return JSONResponse({"error": "Missing required fields: user_id, thread_id, turns"}, status_code=400)

    # Aggregate turns into text
    texts = []
    for t in turns:
        if isinstance(t, dict):
            if "text" in t:
                texts.append(t["text"])
            elif "content" in t:
                texts.append(t["content"])
            else:
                texts.append(json.dumps(t))
        elif isinstance(t, str):
            texts.append(t)
        else:
            texts.append(str(t))
    full_text = "\n\n".join(texts)

    # 1. Segmentation
    segments = segmentation_agent(full_text)

    contour_agent = EpistemicContourAgent()
    assembler_agent = ArtifactAssemblerAgent()
    artifacts = []

    # 2. Epistemic contour filtering & assembly
    for seg in segments:
        seg_json = json.dumps(seg, ensure_ascii=False)
        contour_result = await Runner.run(contour_agent, seg_json)
        seg_out = contour_result.final_output
        if seg_out.is_artifact:
            art_result = await Runner.run(
                assembler_agent,
                json.dumps(seg_out.model_dump(), ensure_ascii=False)
            )
            artifact = art_result.final_output
            artifacts.append(artifact)

    # 3. Bulk insert artifacts into DB
    try:
        db = DBClient()
        # Convert pydantic models to dicts for insertion
        art_dicts = [a.model_dump() for a in artifacts]
        db.insert_artifacts(art_dicts)
    except Exception as e:
        return JSONResponse({"error": f"DB insertion failed: {str(e)}"}, status_code=500)
    finally:
        try:
            db.close()
        except Exception:
            pass

    # 4. Return list of knowledge_ids
    knowledge_ids = [artifact.id for artifact in artifacts]
    return JSONResponse({"knowledge_ids": knowledge_ids})
 
async def health(request: Request):
    """Health check endpoint returning service status."""
    return JSONResponse({"status": "ok"})


app = Starlette(debug=True, routes=[
    Route("/ingest", ingest, methods=["POST"]),
    Route("/health", health, methods=["GET"]),
])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)