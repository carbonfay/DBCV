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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SPEC_PATH = Path(__file__).resolve().parent / "gh.yaml"

app = FastAPI(title="GitHub mini API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/repos/{owner}/{repo}")
async def get_repository(owner: str, repo: str):
    svc = get_github_service()
    try:
       return await svc.get_repository(token=GITHUB_TOKEN, owner=owner, repo=repo)
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
    allow_origins=["*"],  # Allow all origins; restrict in production.
    allow_credentials=False,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, ...).
    allow_headers=["*"],  # Allow all headers.
)


async def getRepo():
    svc = get_github_service()
    try:
       print(await svc.get_repository(token=GITHUB_TOKEN, owner='octocat', repo='Hello-World'))
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        print(HTTPException(status_code=code, detail=str(e)))
    except ApiException as e:
        code = getattr(e, "status", None) or 502
        print(HTTPException(status_code=code, detail=str(e)))
    except Exception as e:
        print("TYPE", type(e))
        breakpoint()

if __name__ == "__main__":
    asyncio.run(getRepo())
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8081)
