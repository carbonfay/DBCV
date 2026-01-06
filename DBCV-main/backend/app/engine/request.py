from httpx import AsyncClient, Response, Limits, Timeout, AsyncHTTPTransport


global_http_client = AsyncClient(
    timeout=Timeout(30.0),
    limits=Limits(
        max_connections=100,           # до 100 одновременных соединений (параллельных)
        max_keepalive_connections=20   # держать открытыми 20 соединений
    ),
)


async def make_request(method, url, params=None, headers=None, content=None, data=None, json_field=None, files=None,
                       proxies=None) -> dict:
    http_client = global_http_client
    if proxies is not None:
        http_client = AsyncClient(
            timeout=Timeout(30.0),
            limits=Limits(
                max_connections=100,  # до 100 одновременных соединений (параллельных)
                max_keepalive_connections=20  # держать открытыми 20 соединений
            ),
            proxies=proxies,
            transport=AsyncHTTPTransport(local_address="0.0.0.0")
        )
    response: Response = await http_client.request(
        method, url, params=params, files=files, content=content, json=json_field, data=data, headers=headers,
    )
    json_result = {"response": response.json()}
    return json_result
