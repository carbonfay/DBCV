import os
from pathlib import Path
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from github_openapi_client.exceptions import ApiException
from app.integrations.github.service import get_github_service

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SPEC_PATH = BASE_DIR / "gh.yaml"

if load_dotenv is not None and ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI(title="GitHub mini API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/repos/{owner}/{repo}/pulls/{pull_number}")
async def get_pull_request(owner: str, repo: str, pull_number: int):
    svc = get_github_service()
    try:
        return await svc.get_pull_request(token=GITHUB_TOKEN, owner=owner, repo=repo, pull_number=pull_number)
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        raise HTTPException(status_code=code, detail=str(e))


@app.get("/openapi.yaml")
async def gh_openapi_yaml() -> Response:
    if not SPEC_PATH.exists():
        return Response(
            content=f"Spec file not found: {SPEC_PATH}",
            status_code=404,
            media_type="text/plain",
        )
    return Response(content=SPEC_PATH.read_text(encoding="utf-8"), media_type="application/yaml")


@app.get("/docs")
async def gh_docs():
    return get_swagger_ui_html(openapi_url="/openapi.yaml", title="GitHub OpenAPI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _debug_get_pull_request():
    svc = get_github_service()
    try:
        print(await svc.get_pull_request(token=GITHUB_TOKEN, owner="carbonfay", repo="DBCV", pull_number=330))
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        print(HTTPException(status_code=code, detail=str(e)))
    except Exception as e:
        import traceback
        traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("TYPE", type(e), traceback_str)
        raise


if __name__ == "__main__":
    asyncio.run(_debug_get_pull_request())
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8081)