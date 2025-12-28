from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from app.integrations.github.service import get_github_service

try:
    from github_openapi_client.exceptions import ApiException
except Exception:
    from app.integrations.github.github_adapter.github_openapi_client.exceptions import ApiException

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SPEC_PATH = BASE_DIR / "gh.yaml"

load_dotenv(dotenv_path=ENV_PATH, override=False)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI(title="GitHub mini API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/repos/{owner}/{repo}/commits")
async def list_commits(
    owner: str,
    repo: str,
    sha: Optional[str] = Query(default=None),
    path: Optional[str] = Query(default=None),
    author: Optional[str] = Query(default=None),
    committer: Optional[str] = Query(default=None),
    since: Optional[datetime] = Query(default=None),
    until: Optional[datetime] = Query(default=None),
    per_page: Optional[int] = Query(default=None, ge=1, le=100),
    page: Optional[int] = Query(default=None, ge=1),
):
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail=f"GITHUB_TOKEN is not set (checked {ENV_PATH})")

    svc = get_github_service()
    try:
        return await svc.list_commits(
            token=GITHUB_TOKEN,
            owner=owner,
            repo=repo,
            sha=sha,
            path=path,
            author=author,
            committer=committer,
            since=since,
            until=until,
            per_page=per_page,
            page=page,
        )
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        detail = getattr(e, "body", None) or str(e)
        raise HTTPException(status_code=code, detail=detail)


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


async def _debug_list_commits():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")

    svc = get_github_service()
    try:
        print(await svc.list_commits(token=GITHUB_TOKEN, owner="octocat", repo="Hello-World", per_page=5, page=1))
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        detail = getattr(e, "body", None) or str(e)
        print(HTTPException(status_code=code, detail=detail))
    except Exception as e:
        import traceback
        traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("TYPE", type(e), traceback_str)
        raise

if __name__ == "__main__":
    asyncio.run(_debug_list_commits())
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8081)
