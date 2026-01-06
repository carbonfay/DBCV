"""Handler для выполнения интеграций через библиотеки."""
from typing import Dict, Any, Union
from uuid import UUID

from app.engine.bot_processor import ConnectionHandler
from app.engine.variables import replace_variables_universal
from app.utils.dict import deep_merge_dicts
from app.integrations.registry import registry
from app.auth.credentials_resolver import CredentialsResolver
from app.managers.data_manager import DataManager
from app.loggers.bot import BotLogger
from app.schemas.connection import ConnectionGroupExport


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
        
        # Получаем credentials resolver
        resolver = CredentialsResolver(self.data_manager)
        
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
            return result
        except Exception as e:
            await self.logger.error(f"Integration execution error: {e}")
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await self.logger.error(f"Traceback: {traceback_str}")
            return None

