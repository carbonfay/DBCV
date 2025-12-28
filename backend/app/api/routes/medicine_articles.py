from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/articles", tags=["medicine"])

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def _fetch_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as err:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error: {err}") from err
    except httpx.RequestError as err:
        raise HTTPException(status_code=502, detail=f"Upstream request error: {err}") from err

    try:
        data = response.json()
    except ValueError as err:
        raise HTTPException(status_code=502, detail="Invalid JSON from upstream") from err

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected upstream response format")

    return data


def _build_article(item: Dict[str, Any], uid: str) -> Dict[str, Any]:
    authors_raw = item.get("authors") or []
    authors: List[str] = []
    for author in authors_raw:
        if isinstance(author, dict) and author.get("name"):
            authors.append(author["name"])

    return {
        "id": uid,
        "title": item.get("title"),
        "pubdate": item.get("pubdate"),
        "source": item.get("source"),
        "authors": authors,
        "elocationid": item.get("elocationid"),
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
    }


@router.get("")
async def get_articles(
    query: Optional[str] = Query(default=None, description="Search term"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: str = Query(default="pubmed"),
    sort: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
    api_key: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    term = query or "medicine"
    retstart = (page - 1) * page_size

    search_params: Dict[str, Any] = {
        "db": db,
        "term": term,
        "retmode": "json",
        "retstart": retstart,
        "retmax": page_size,
    }
    if sort:
        search_params["sort"] = sort
    if email:
        search_params["email"] = email
    if api_key:
        search_params["api_key"] = api_key

    search_data = await _fetch_json(f"{EUTILS_BASE}/esearch.fcgi", search_params)
    esearch = search_data.get("esearchresult", {})
    ids = esearch.get("idlist", []) if isinstance(esearch, dict) else []
    try:
        count = int(esearch.get("count", 0)) if isinstance(esearch, dict) else 0
    except (TypeError, ValueError):
        count = 0

    articles: List[Dict[str, Any]] = []
    if ids:
        summary_params: Dict[str, Any] = {
            "db": db,
            "id": ",".join(ids),
            "retmode": "json",
        }
        if email:
            summary_params["email"] = email
        if api_key:
            summary_params["api_key"] = api_key

        summary_data = await _fetch_json(f"{EUTILS_BASE}/esummary.fcgi", summary_params)
        result = summary_data.get("result", {})
        uids = result.get("uids", []) if isinstance(result, dict) else []
        for uid in uids:
            item = result.get(uid) if isinstance(result, dict) else None
            if isinstance(item, dict):
                articles.append(_build_article(item, uid))

    return {
        "query": term,
        "count": count,
        "page": page,
        "page_size": page_size,
        "ids": ids,
        "articles": articles,
    }
