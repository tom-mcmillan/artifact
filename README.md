#!/usr/bin/env markdown
# artifacting

artifacting is a Python package and HTTP service for processing user session data into structured knowledge artifacts.

## Installation

Install in editable mode from the project root:
```bash
pip install -e .
```

## Running the API server

From the **project root directory** (not inside subfolders), start the service:
```bash
uvicorn artifacting.orchestration.api:app --port 8001
```

### Important

- Ensure you run the command from the repository root.  Running it inside the `orchestration/` folder will shadow the `artifacting` package import and lead to import errors.

## Requirements

See `requirements.txt` or `pyproject.toml` for full dependency list.