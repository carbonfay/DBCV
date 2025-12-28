import os
from pathlib import Path
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
from github_openapi_client.exceptions import ApiException
from github_openapi_client.models.issues_create_request import IssuesCreateRequest
from github_openapi_client.models.issues_create_request_title import IssuesCreateRequestTitle
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


@app.post("/repos/{owner}/{repo}/issues")
async def create_issue(owner: str, repo: str, body: dict):
    svc = get_github_service()
    try:
        req = IssuesCreateRequest.from_dict(body) if hasattr(IssuesCreateRequest, "from_dict") else IssuesCreateRequest(**body)
        return await svc.create_issue(token=GITHUB_TOKEN, owner=owner, repo=repo, request=req)
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


async def _debug_create_issue():
    svc = get_github_service()
    try:
        req = IssuesCreateRequest(
            title=IssuesCreateRequestTitle("Test issue from adapter"),
            body="created via local adapter",
        )
        print(await svc.create_issue(token=GITHUB_TOKEN, owner="octocat", repo="Hello-World", request=req))
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        print(HTTPException(status_code=code, detail=str(e)))
    except Exception as e:
        import traceback
        traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("TYPE", type(e), traceback_str)
        raise


if __name__ == "__main__":
    asyncio.run(_debug_create_issue())
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8081)
