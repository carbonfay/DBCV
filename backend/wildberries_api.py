"""Mock библиотека для тестирования Wildberries интеграции.

Эта библиотека имитирует поведение реального Wildberries API клиента
для целей тестирования и разработки.
"""

import time
from typing import Optional, Dict, Any


class WildberriesAPIError(Exception):
    """Базовое исключение Wildberries API."""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(WildberriesAPIError):
    """Ошибка аутентификации."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class ValidationError(WildberriesAPIError):
    """Ошибка валидации данных."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)


class Client:
    """Mock клиент Wildberries API.
    
    Имитирует основные методы реального клиента для тестирования.
    """
    
    def __init__(self, api_key: str):
        """Инициализация клиента.
        
        Args:
            api_key: API ключ Wildberries
            
        Raises:
            AuthenticationError: Если API ключ невалидный
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        if api_key == "invalid" or len(api_key) < 10:
            raise AuthenticationError("Invalid API key format")
        
        self.api_key = api_key
        self._request_count = 0
    
    def update_stock(
        self,
        sku: str,
        stock: int,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Обновляет остатки товара.
        
        Args:
            sku: Артикул товара (SKU)
            stock: Количество на складе
            warehouse_id: ID склада (опционально)
            
        Returns:
            Словарь с результатом операции
            
        Raises:
            ValidationError: Если данные невалидны
            WildberriesAPIError: При других ошибках API
        """
        self._request_count += 1
        
        # Валидация входных данных
        if not sku or not isinstance(sku, str):
            raise ValidationError("SKU must be a non-empty string")
        
        if not isinstance(stock, int) or stock < 0:
            raise ValidationError("Stock must be a non-negative integer")
        
        if warehouse_id is not None and not isinstance(warehouse_id, str):
            raise ValidationError("Warehouse ID must be a string")
        
        # Имитация задержки сети
        time.sleep(0.1)
        
        # Имитация различных ответов
        if sku.startswith("ERROR"):
            raise WildberriesAPIError(
                f"Failed to update stock for SKU {sku}",
                status_code=500
            )
        
        if sku.startswith("NOTFOUND"):
            raise WildberriesAPIError(
                f"SKU {sku} not found",
                status_code=404
            )
        
        # Успешный ответ
        result = {
            "sku": sku,
            "stock": stock,
            "updated": True,
            "timestamp": int(time.time()),
            "message": f"Stock updated successfully for SKU {sku}",
            "request_id": f"req_{self._request_count}"
        }
        
        if warehouse_id:
            result["warehouse_id"] = warehouse_id
        
        return result
    
    def get_stock(self, sku: str) -> Dict[str, Any]:
        """Получает текущие остатки товара.
        
        Args:
            sku: Артикул товара (SKU)
            
        Returns:
            Словарь с информацией об остатках
        """
        if not sku:
            raise ValidationError("SKU is required")
        
        # Имитация ответа
        return {
            "sku": sku,
            "stock": 100,  # Mock значение
            "available": 95,
            "reserved": 5,
            "warehouses": [
                {"id": "WH001", "stock": 60},
                {"id": "WH002", "stock": 40}
            ]
        }
    
    def batch_update_stock(
        self,
        updates: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Массовое обновление остатков.
        
        Args:
            updates: Список словарей с обновлениями
                     [{"sku": "...", "stock": 100, "warehouse_id": "..."}]
                     
        Returns:
            Словарь с результатами операции
        """
        if not updates or not isinstance(updates, list):
            raise ValidationError("Updates must be a non-empty list")
        
        results = []
        errors = []
        
        for update in updates:
            try:
                result = self.update_stock(
                    sku=update.get("sku"),
                    stock=update.get("stock"),
                    warehouse_id=update.get("warehouse_id")
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "sku": update.get("sku"),
                    "error": str(e)
                })
        
        return {
            "total": len(updates),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }


# Версия mock библиотеки
__version__ = "1.0.0-mock"


# Для совместимости
def create_client(api_key: str) -> Client:
    """Создает клиент Wildberries API.
    
    Args:
        api_key: API ключ
        
    Returns:
        Экземпляр Client
    """
    return Client(api_key)
</contents>