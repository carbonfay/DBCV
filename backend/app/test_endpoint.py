#!/usr/bin/env python3
"""
Скрипт для тестирования endpoint'ов с авторизацией.
Использование:
    python test_endpoint.py GET /api/v1/integrations/catalog
    python test_endpoint.py POST /api/v1/steps/{step_id}/run '{"bot_id": "...", "variables": {}}'
"""
import asyncio
import json
import sys
from typing import Optional

import httpx


async def get_auth_token(username: str = "test", password: str = "testtest", base_url: str = "http://localhost:8003") -> str:
    """Получить токен авторизации."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v1/login/access-token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code != 200:
            print(f"❌ Ошибка авторизации: {response.status_code}")
            print(response.text)
            sys.exit(1)
        token_data = response.json()
        return token_data["access_token"]


async def test_endpoint(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    username: str = "test",
    password: str = "testtest",
    base_url: str = "http://localhost:8003"
):
    """Тестировать endpoint с авторизацией."""
    # Получаем токен
    print(f"🔐 Авторизация под пользователем {username}...")
    token = await get_auth_token(username, password, base_url)
    print(f"✓ Токен получен: {token[:20]}...")
    
    # Формируем URL
    if not endpoint.startswith("http"):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{base_url}{endpoint}"
    else:
        url = endpoint
    
    # Формируем заголовки
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Выполняем запрос
    print(f"\n📡 {method} {url}")
    if data:
        print(f"📦 Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            else:
                print(f"❌ Неподдерживаемый метод: {method}")
                sys.exit(1)
            
            print(f"\n📊 Status: {response.status_code}")
            print(f"📋 Headers: {dict(response.headers)}")
            
            try:
                result = response.json()
                print(f"\n✅ Response JSON:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except:
                print(f"\n📄 Response Text:")
                print(response.text[:1000])
                if len(response.text) > 1000:
                    print(f"... (показано первые 1000 символов из {len(response.text)})")
            
            return response
            
        except httpx.RequestError as e:
            print(f"❌ Ошибка запроса: {e}")
            sys.exit(1)


async def main():
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python test_endpoint.py <METHOD> <ENDPOINT> [JSON_BODY]")
        print("\nПримеры:")
        print('  python test_endpoint.py GET /api/v1/integrations/catalog')
        print('  python test_endpoint.py POST /api/v1/steps/123/run \'{"bot_id": "...", "variables": {}}\'')
        print('  python test_endpoint.py GET /api/v1/steps')
        sys.exit(1)
    
    method = sys.argv[1]
    endpoint = sys.argv[2]
    data = None
    
    if len(sys.argv) > 3:
        try:
            data = json.loads(sys.argv[3])
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            sys.exit(1)
    
    await test_endpoint(method, endpoint, data)


if __name__ == "__main__":
    asyncio.run(main())

