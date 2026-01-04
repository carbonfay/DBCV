"""Handler для выполнения интеграций через библиотеки."""
from typing import Dict, Any, Union, Optional, Mapping
from uuid import UUID

from app.engine.bot_processor import ConnectionHandler
from app.engine.variables import replace_variables_universal
from app.utils.dict import deep_merge_dicts
from app.integrations.registry import registry
from app.auth.credentials_resolver import CredentialsResolver
from app.managers.data_manager import DataManager
from app.loggers.bot import BotLogger
from app.schemas.connection import ConnectionGroupExport
from app.integrations.base import IntegrationMetadata


class StepAwareCredentialsResolver:
    """
    Обертка над CredentialsResolver, которая учитывает step.credential_id.
    
    Переопределяет get_default_for и get_single_for, чтобы сначала проверять
    явно указанный credential для шага.
    """
    
    def __init__(self, resolver: CredentialsResolver, step_credential_id: Optional[UUID], integration_metadata: IntegrationMetadata, bot_id: UUID, logger: BotLogger):
        self._resolver = resolver
        self._step_credential_id = step_credential_id
        self._integration_metadata = integration_metadata
        self._bot_id = bot_id
        self._logger = logger
        self._used_step_credential = False
    
    async def get_by_id(self, cred_id: UUID) -> Optional[Mapping[str, Any]]:
        """Прямой вызов get_by_id без изменений."""
        return await self._resolver.get_by_id(cred_id)
    
    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        """
        Получает credential с учетом step.credential_id.
        
        Приоритет:
        1. step.credential_id (если указан и совместим)
        2. Default credential бота
        """
        # Если есть step.credential_id и он еще не использован, проверяем его
        if self._step_credential_id and not self._used_step_credential:
            try:
                cred = await self._resolver.get_by_id(UUID(str(self._step_credential_id)))
                if cred:
                    # Проверяем совместимость для provider != "other"
                    if self._integration_metadata.credentials_provider != "other":
                        cred_provider = cred.get("provider")
                        cred_strategy = cred.get("strategy")
                        if (
                            cred_provider == self._integration_metadata.credentials_provider and
                            cred_strategy == self._integration_metadata.credentials_strategy
                        ):
                            self._used_step_credential = True
                            await self._logger.info(f"Using step credential {self._step_credential_id} for integration")
                            return cred
                        else:
                            await self._logger.warning(
                                f"Step credential {self._step_credential_id} is not compatible. "
                                f"Expected provider={self._integration_metadata.credentials_provider}, "
                                f"strategy={self._integration_metadata.credentials_strategy}, "
                                f"but got provider={cred_provider}, strategy={cred_strategy}. "
                                f"Falling back to default."
                            )
                    else:
                        # Для provider="other" можно использовать любой credential
                        self._used_step_credential = True
                        await self._logger.info(f"Using step credential {self._step_credential_id} for integration")
                        return cred
            except Exception as e:
                await self._logger.warning(f"Failed to get step credential {self._step_credential_id}: {e}. Falling back to default.")
        
        # Fallback на default credential
        return await self._resolver.get_default_for(bot_id=bot_id, provider=provider, strategy=strategy)
    
    async def get_single_for(self, *, bot_id: UUID, provider: str, strategy: str | None) -> Optional[Mapping[str, Any]]:
        """
        Получает credential с учетом step.credential_id.
        
        Приоритет:
        1. step.credential_id (если указан и совместим)
        2. Default credential бота
        3. Автоматический выбор
        """
        # Сначала пробуем get_default_for (который уже учитывает step.credential_id)
        result = await self.get_default_for(bot_id=bot_id, provider=provider, strategy=strategy)
        if result:
            return result
        
        # Fallback на get_single_for
        return await self._resolver.get_single_for(bot_id=bot_id, provider=provider, strategy=strategy)


class ConnectionIntegrationHandler(ConnectionHandler):
    """Handler для интеграций, использующих библиотеки напрямую."""
    
    def __init__(self, logger: BotLogger, data_manager: DataManager, bot_id: Union[UUID, str]):
        self.logger = logger
        self.data_manager = data_manager
        # Преобразуем bot_id в UUID если это строка
        if isinstance(bot_id, str):
            try:
                self.bot_id = UUID(bot_id)
            except ValueError:
                self.bot_id = bot_id  # Оставляем как есть, если не валидный UUID
        else:
            self.bot_id = bot_id
    
    async def handle(
        self,
        connection_group: ConnectionGroupExport,
        context: dict,
        all_variables: dict = {}
    ) -> Dict[str, Any] | None:
        """
        Выполняет интеграцию через библиотеку.
        
        Args:
            connection_group: Группа связей с интеграцией
            context: Контекст выполнения
            all_variables: Все переменные
        
        Returns:
            Результат выполнения интеграции или None при ошибке
        """
        integration_id = connection_group.integration_id
        integration_config = connection_group.integration_config or {}
        
        if not integration_id:
            await self.logger.error("integration_id not found in connection_group")
            return None
        
        # Получаем интеграцию из реестра
        integration = registry.get(integration_id)
        
        if not integration:
            await self.logger.error(f"Integration {integration_id} not found in registry")
            return None
        
        # Подставляем переменные в конфигурацию интеграции
        # Объединяем context и all_variables для подстановки
        merged_context = deep_merge_dicts(context, all_variables)
        
        try:
            # Подставляем переменные в config (рекурсивно для всех значений)
            substituted_config = await replace_variables_universal(integration_config, merged_context)
            await self.logger.info(f"Config after variable substitution: {substituted_config}")
        except Exception as e:
            await self.logger.error(f"Error substituting variables in integration config: {e}")
            substituted_config = integration_config  # Используем оригинальный config при ошибке
        
        # Получаем credential_id из step (если указан)
        step_credential_id = None
        if connection_group.step and hasattr(connection_group.step, 'credential_id'):
            step_credential_id = connection_group.step.credential_id
        
        # Получаем metadata интеграции
        metadata = integration.metadata
        
        # Создаем обертку над resolver, которая учитывает step.credential_id
        base_resolver = CredentialsResolver(self.data_manager)
        step_cred_uuid = None
        if step_credential_id:
            try:
                step_cred_uuid = UUID(str(step_credential_id))
            except (ValueError, TypeError):
                await self.logger.warning(f"Invalid step credential_id format: {step_credential_id}")
                step_cred_uuid = None
        
        resolver = StepAwareCredentialsResolver(
            resolver=base_resolver,
            step_credential_id=step_cred_uuid,
            integration_metadata=metadata,
            bot_id=self.bot_id,
            logger=self.logger
        )
        
        # Выполняем интеграцию (библиотека используется внутри)
        try:
            await self.logger.info(f"Executing integration {integration_id}...")
            result = await integration.execute(
                config=substituted_config,
                credentials_resolver=resolver,
                bot_id=self.bot_id,
                logger=self.logger
            )
            await self.logger.info(f"Integration {integration_id} executed successfully")
            
            # Извлекаем полезные данные из структуры ответа
            # Интеграции возвращают: {"response": {"ok": True, "result": {...}}}
            if isinstance(result, dict) and "response" in result:
                response = result["response"]
                if isinstance(response, dict):
                    if response.get("ok") and "result" in response:
                        # Возвращаем только данные результата для успешных запросов
                        return response["result"]
                    elif not response.get("ok"):
                        # Для ошибок возвращаем полную структуру с описанием ошибки
                        return {
                            "error": True,
                            "error_code": response.get("error_code", 500),
                            "description": response.get("description", "Unknown error")
                        }
            
            # Если структура неожиданная, возвращаем как есть
            return result
        except Exception as e:
            await self.logger.error(f"Integration execution error: {e}")
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await self.logger.error(f"Traceback: {traceback_str}")
            return None

