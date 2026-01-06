import json
import logging
import traceback
from abc import abstractmethod, ABC
import random
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, Dict
from uuid import uuid4

from jqqb_evaluator.evaluator import Evaluator
from redis.asyncio import Redis

from app.auth.credentials_resolver import CredentialsResolver
from app.auth.service import AuthService
from app.config import settings

from app.database import sessionmanager
from app.engine.request import make_request
from app.engine.variables import variable_substitution_pydantic, update_variables_dict, variable_substitution
from app.loggers import BotLogger
from app.loggers.bot import NoopBotLogger
from app.managers.data_manager import DataManager
from app.managers.message_manager import MessageManager
from app.models.base import UUID
from app.models.connection import SearchType
from app.schemas.bot import BotProcessor
from app.schemas.channel import ChannelSimple
from app.schemas.session import SessionSimple
from app.schemas.connection import ConnectionExport, ConnectionGroupExport
from app.schemas.request import RequestSubstitute
from app.schemas.step import StepExport, StepTemplate
from app.services.message_service import MessageService
from app.services.attachment_repository_sql import SqlAttachmentRepository
from app.services.s3_storage_service import S3StorageService
from sqlalchemy import text
from app.database import sessionmanager
from app.schemas.templates import TemplateInstancePublic
from app.utils.dict import deep_merge_dicts, get_value_by_list_keys, deep_set, get_value_by_path
from app.engine.safe_env import safe_globals

redis = Redis.from_url(settings.CACHE_REDIS_URL)
logger = logging.getLogger(__name__)


class ConnectionHandler(ABC):
    @abstractmethod
    async def handle(self, connection_group: ConnectionGroupExport, context: dict,
                     all_variables: dict = {}):
        raise NotImplementedError("Subclasses must implement this method")


class ConnectionResponseHandler(ConnectionHandler):
    def __init__(self, bot: BotProcessor, auth: AuthService, data_manager: DataManager, logger: Optional[BotLogger] = None, ):
        self.logger = logger or NoopBotLogger()
        self.auth = auth
        self.data_manager = data_manager
        self.bot = bot

    async def handle(self, connection_group: ConnectionGroupExport, context: dict,
                     all_variables: dict = {}):
        await self.logger.info("Working response handler...")

        try:
            if connection_group.request:
                request_in: RequestSubstitute = await variable_substitution_pydantic(
                    RequestSubstitute.model_validate(connection_group.request.__dict__),
                    context=deep_merge_dicts(context, all_variables)
                )
        except Exception as e:
            await self.logger.error(f"Error in response handler: {e}")
            return {"response": None}
        try:
            if self.auth:
                bot_id = self.bot.id
                if bot_id:
                    headers = {}
                    await self.auth.apply(
                        bot_id=str(bot_id),
                        headers=headers,
                        request_url=request_in.request_url,
                        credentials_id=context.get("credentials_id"),      # если явно указали
                        strategy_hint=context.get("auth_strategy"),        # "service_account" | "oauth"
                        profile=context.get("auth_profile", "default"),
                        hints=context.get("auth_hints", {}),
                    )
                    if headers:
                        request_in.headers = headers
        except Exception as e:
            await self.logger.error(f"Auth injection failed: {e}")

        try:
            files = await self._prepare_request_files(request_in.attachments)
        except Exception as e:
            await self.logger.error(f"Error in prepare request files handler: {e}")
        try:
            result_json = await make_request(
                connection_group.request.method,
                request_in.request_url,
                params=request_in.params,
                json_field=request_in.json_field,
                content=request_in.content,
                data=request_in.data,
                files=files,
                headers=request_in.headers,
                proxies=request_in.proxies
            )
            await self.logger.info(f"Response: {result_json}")
            for file in files:
                file[1].close()
            return result_json
        except Exception as e:
            await self.logger.error(f"Error in response handler: {e}")
            return None

    async def _prepare_request_files(self, attachments: list | None):
        files = []
        if not attachments:
            return files

        # attachments can be IDs or variable placeholders already substituted into dicts
        repo = SqlAttachmentRepository(sessionmanager.engine)
        storage = S3StorageService()

        for att in attachments:
            attachment_id = att.get("id") if isinstance(att, dict) else att
            if not attachment_id:
                continue

            meta = await repo.get_by_id(attachment_id)
            if not meta:
                await self.logger.info(f"Attachment not found: {attachment_id}")
                continue

            key = meta.key
            content_type = meta.content_type or "application/octet-stream"
            data = await storage.get_bytes(key)
            filename = key.split("/")[-1] if isinstance(key, str) else "file"

            # httpx files format supports tuples: (name, bytes, content_type)
            files.append(("files", (filename, data, content_type)))
        return files


class ConnectionCodeHandler(ConnectionHandler):
    def __init__(self, logger):
        self.logger = logger

    async def handle(self, connection_group: ConnectionGroupExport, context: dict,
                     all_variables: dict = {}):
        await self.logger.info("Working code handler...")
        try:
            if connection_group.code:
                return await CodeExecutor(self.logger).execute(connection_group.code, context,
                                                                               deepcopy(all_variables))
        except Exception as e:

            await self.logger.error(f"Error in code handler: {e}")
            return None


class CodeExecutorBase(ABC):
    @abstractmethod
    async def execute(self, code: str, context: Optional[Dict[str, Any]] = None,
                      variables: Optional[Dict[str, Any]] = None) -> Any:
        pass


class CodeExecutor(CodeExecutorBase):
    def __init__(self, logger: BotLogger):
        self.logger = logger
        self.available_globals = safe_globals
        self.available_globals[self.logger.print.__name__] = self.logger.print

    async def execute(self, code: str, context: dict | None = None, variables: dict | None = None):
        available_variables = {}
        context = context or {}
        variables = variables or {}
        try:
            exec(compile(code, '<string>', 'exec'),
                 {"__builtins__": None, **self.available_globals},
                 available_variables)

            if 'main' not in available_variables:
                await self.logger.error("Error: функция 'main' не определена.")
                return context

            result = await available_variables['main'](context, variables=variables)
            return result

        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print(traceback_str)
            await self.logger.error(f"Execution error:\n{traceback_str}")
            return context


class ConnectionHandlerFactory:
    @staticmethod
    def get_handler(search_type: SearchType, logger,
                    bot: BotProcessor | None = None,
                    auth: AuthService | None = None,
                    data_manager: DataManager | None = None) -> ConnectionHandler | None:
        match search_type:
            case SearchType.message:
                return None
            case SearchType.response:
                return ConnectionResponseHandler(bot, auth, data_manager, logger)
            case SearchType.code:
                return ConnectionCodeHandler(logger)
            case SearchType.integration:
                from app.engine.integration_handler import ConnectionIntegrationHandler
                # Получаем bot_id из bot или из data_manager через context
                bot_id = None
                if bot:
                    bot_id = bot.id
                elif data_manager:
                    # Пытаемся получить из текущего контекста (если доступен)
                    # В большинстве случаев bot будет передан
                    pass
                if not bot_id:
                    if hasattr(logger, 'error'):
                        logger.error("Bot ID is required for integration handler")
                    return None
                return ConnectionIntegrationHandler(logger, data_manager, bot_id)
            case _:
                raise ValueError(f"Unsupported search type: {search_type}")


class BaseProcessor(ABC):
    @abstractmethod
    async def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def _save_variables(self, variables_save_as: dict[str, str], context: dict[str, Any]):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _get_current_step(self, *args, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def _switch_to_next_step(self, next_step: StepExport):
        raise NotImplementedError("Subclasses must implement this method")


class Processor(BaseProcessor):
    def __init__(self, logger, all_variables, data_manager):
        self.data_manager: DataManager = data_manager
        self.logger: BotLogger = logger
        self.all_variables = all_variables
        self.current_step = None
        self.context: dict[str, Any] = {}
        self.message: dict[str, Any] = {}

    async def _save_variables(self, variables_save_as: dict[str, str], context: dict[str, Any]):
        await self.logger.info("Save variables...")
        try:
            if variables_save_as:
                if isinstance(variables_save_as, str):
                    variables_save_as = json.loads(variables_save_as)
                self.all_variables = await update_variables_dict(
                    self.all_variables, None, variables_save_as, context
                )

                await self.logger.info("Variables updated locally in memory.")
                await self.logger.send_variables(self.all_variables)
        except Exception as e:
            await self.logger.info(f"Error in save variables: {e}")

    async def switch_to_next_step(self, connection: ConnectionExport) -> bool:
        await self.logger.info("Switch to next step...")
        next_step = self._get_current_step(connection.next_step_id)
        return await self._switch_to_next_step(next_step)

    async def _evaluate_and_switch(self, connection: ConnectionExport, context: dict) -> bool:
        await self.logger.info("Check rules and context")
        rules_str = connection.rules
        if not rules_str or not context:
            return await self.switch_to_next_step(connection)

        await self.logger.info("Create context")

        safe_all_variables = self.all_variables if self.all_variables is not None else {}
        for key, value in safe_all_variables.items():
            if value is None:
                safe_all_variables[key] = {}
        context = deep_merge_dicts(safe_all_variables, context or None)
        await self.logger.info("Substitution variables...")

        try:
            rules_str = await variable_substitution(rules_str, context)
            evaluator = Evaluator(json.loads(rules_str))
        except Exception as e:
            await self.logger.error(f"Error variable substitution: {e}")
            return False

        await self.logger.info("Working evaluator...")
        try:
            if evaluator.object_matches_rules(context):
                return await self.switch_to_next_step(connection)
        except Exception as e:
            await self.logger.error(f"Error evaluating rules: {e}")
            return False

        return False

    async def process_connection_groups(self, connection_groups: list[ConnectionGroupExport], context: dict):
        for connection_group in connection_groups:
            await self.logger.info("Processing connection group...")
            resolver = CredentialsResolver(self.data_manager)
            auth_service = AuthService(resolver)
            handler = ConnectionHandlerFactory.get_handler(connection_group.search_type, self.logger, self.bot, auth_service, self.data_manager)
            if handler:
                self.context = await handler.handle(connection_group, context, self.all_variables)
            await self._save_variables(connection_group.variables, self.context)
            await self.logger.info("Start evaluate rules and switch step...")

            for connection in connection_group.connections:
                if await self._evaluate_and_switch(connection, self.context):
                    return True

        await self.logger.info("No connection matched in group.")
        return False

    async def _switch_to_next_step(self, next_step: StepExport):
        """
            Выполняет переход к следующему шагу.
        """
        if not next_step:
            await self.logger.warning("Next step not found.")
            return False

        self.current_step = next_step

        safe_all_variables = self.all_variables if self.all_variables is not None else {}
        for key, value in safe_all_variables.items():
            if value is None:
                safe_all_variables[key] = {}
        context = deep_merge_dicts(safe_all_variables, self.message)

        if next_step.message:
            await self.logger.info("Create step message...")
            message_service = MessageService(engine=sessionmanager.engine)
            await message_service.send_message(self.session, next_step.message, context=context)

    def _get_current_step(self, step_id: str) -> StepTemplate:
        ...

    async def run(self, context: dict, variables: dict) -> dict:
        ...


class TemplateProcessor(Processor):
    def __init__(self, template, logger, data_manager: DataManager, bot):
        super().__init__(logger, {}, data_manager)
        self.logger = logger
        self.bot = bot
        self.instance: TemplateInstancePublic = template
        self.context: dict[str, Any] = {}
        self.current_step: StepExport | None = None
        self.all_variables: dict[str, Any] = {}

    def _get_current_step(self, step_id: str) -> StepTemplate:
        for step in self.instance.steps:
            if step.id == step_id:
                return step

    @staticmethod
    def _extract_inputs_from_mapping(mapping: dict, variables: dict) -> dict:
        """
        Рекурсивно извлекает значения из внешних переменных по mapping с path/default.
        """

        def resolve(mapping_block: dict) -> dict:
            result = {}
            for key, value in mapping_block.items():
                if isinstance(value, dict) and "path" in value:
                    path = value.get("path")
                    default = value.get("default")
                    val = get_value_by_list_keys(variables, path.split(".")) if path else default
                    result[key] = val if val is not None else default
                elif isinstance(value, dict):  # вложенный словарь без path
                    result[key] = resolve(value)
            return result

        return resolve(mapping)

    @staticmethod
    def _extract_outputs_to_mapping(mapping: dict, variables: dict) -> dict:
        """
        Формирует вложенный результат, извлекая значения из переменных по ключам mapping,
        и помещая их в структуру результата по указанному path.
        """
        output = {}

        def recurse(node: dict, current_vars: dict, parent_keys=[]):
            for key, val in node.items():
                if isinstance(val, dict) and "path" in val:
                    source_path = parent_keys + [key]
                    value = get_value_by_path(current_vars, ".".join(source_path))
                    if value is None:
                        value = val.get("default")
                    if val.get("path"):
                        deep_set(output, val["path"], value)
                elif isinstance(val, dict):
                    recurse(val, current_vars, parent_keys + [key])

        recurse(mapping, variables)
        return output

    async def run(self, context: dict, variables: dict) -> dict:
        """
        Выполняет логику шаблона. Подставляет inputs, исполняет логику, возвращает outputs.
        """
        await self.logger.info("Extract inputs from mapping...")

        self.all_variables = {"template": self._extract_inputs_from_mapping(self.instance.inputs_mapping.model_dump(),
                                                                            variables)}
        self.context = context

        self.current_step = self._get_current_step(self.instance.first_step_id)
        await self.logger.info("Process connection groups...")

        await self.process_connection_groups(self.current_step.connection_groups, self.context)

        outputs = self._extract_outputs_to_mapping(self.instance.outputs_mapping.model_dump(), self.all_variables.get("template"))
        return outputs


class MessageProcessor(Processor):
    def __init__(self, sender_id: str,
                 bot: dict[str, Any],
                 channel: dict[str, Any],
                 message: dict[str, Any],
                 data_manager: DataManager):
        super().__init__(logger, {}, data_manager)
        self.sender_id = sender_id
        cache_structure = bot.get("cache_structure")
        if not isinstance(cache_structure, dict):
            raise ValueError(f"Invalid bot id-{bot.get('id')}: missing cache_structure")
        self.bot = BotProcessor(**cache_structure)
        self.channel = ChannelSimple(**channel)
        self.message: dict[str, Any] = message
        self.all_variables = None
        self.session = None
        self.current_step = None
        self.context: dict[str, Any] = {}

        self.logger: BotLogger = BotLogger(self.bot.id)

    async def _switch_to_next_step(self, next_step: StepExport):
        """
            Выполняет переход к следующему шагу.
        """
        if not next_step:
            await self.logger.warning("Next step not found.")
            return False

        self.current_step = next_step

        self.logger.set_step(self.current_step.id)

        safe_all_variables = self.all_variables if self.all_variables is not None else {}
        for key, value in safe_all_variables.items():
            if value is None:
                safe_all_variables[key] = {}
        context = deep_merge_dicts(safe_all_variables, self.message)

        if next_step.message:
            await self.logger.info("Create step message...")
            message_service = MessageService(engine=sessionmanager.engine)
            await message_service.send_message(self.session, next_step.message, context=context)
        if next_step.template_instance:
            await self.logger.info("Processing template...")

            template_processor = TemplateProcessor(next_step.template_instance, self.logger, self.data_manager, self.bot)
            template_outputs = await template_processor.run(self.context, self.all_variables)
            safe_all_variables = self.all_variables if self.all_variables is not None else {}
            safe_template_outputs = template_outputs if template_outputs is not None else {}
            self.all_variables = deep_merge_dicts(safe_all_variables, safe_template_outputs)
            return await self.process_connection_groups(next_step.connection_groups, self.context)

        if next_step.is_proxy:
            await self.logger.info("Processing connection groups for proxy step...")
            return await self.process_connection_groups(next_step.connection_groups, self.context)

        return True

    def _get_current_step(self, step_id):
        for step in self.bot.steps:
            if step.id == step_id:
                return step

    async def run(self, *args, **kwargs):
        await self.logger.info("Start working bot...")
        await self.logger.info("Get or create session...")

        self.session = SessionSimple(
            **(await self.data_manager.get_or_create_session(self.sender_id, self.bot.id, self.channel.id,
                                                             self.bot.first_step_id)))

        await self.logger.info("Load variables...")
        self.all_variables = await self.data_manager.get_all_variables(self.sender_id, self.bot.id, self.channel.id,
                                                                       self.session.id)
        if self.all_variables is None:
            self.all_variables = {}
        for key, value in self.all_variables.items():
            if value is None:
                self.all_variables[key] = {}
        self.context = self.message
        await self.logger.info("Check master groups...")
        if await self.process_connection_groups(self.bot.master_connection_groups, self.context):
            await self.data_manager.update_all_variables(self.sender_id, self.bot.id, self.channel.id,
                                                         self.session.id, self.all_variables)
            self.session.step_id = self.current_step.id
            await self.data_manager.update_session(self.session.user_id,
                                                   self.session.bot_id,
                                                   self.session.channel_id,
                                                   self.session.step_id)
            return

        await self.logger.info("Check groups...")
        self.current_step = self._get_current_step(self.session.step_id)

        self.logger.set_step(self.current_step.id)

        if await self.process_connection_groups(self.current_step.connection_groups, self.context):
            await self.data_manager.update_all_variables(self.sender_id, self.bot.id, self.channel.id,
                                                         self.session.id, self.all_variables)
            self.session.step_id = self.current_step.id
            await self.data_manager.update_session(self.session.user_id,
                                                   self.session.bot_id,
                                                   self.session.channel_id,
                                                   self.session.step_id)
            return

        await self.logger.info("No transitions triggered, committing any updated variables.")
        await self.data_manager.update_all_variables(self.sender_id, self.bot.id, self.channel.id,
                                                     self.session.id, self.all_variables)
        self.session.step_id = self.current_step.id
        await self.data_manager.update_session(self.session.user_id,
                                               self.session.bot_id,
                                               self.session.channel_id,
                                               self.session.step_id)


async def check_message(message: dict, channel_id: UUID | str | None = None):
    """Check and process a message."""
    data_manager = DataManager(redis, sessionmanager.engine)

    channel = await data_manager.get_channel(channel_id)
    logger.info("Start check message")
    if not channel:
        logger.warning("Channel not found.")
        return

    message_obj = message.get("message")
    if not message_obj:
        logger.warning("Message content is empty.")
        return

    recipient_id = message_obj.get("recipient_id")
    sender_id = message_obj.get("sender_id")
    if not recipient_id:
        default_bot_id = channel.get("default_bot_id")
        bot = await data_manager.get_bot(default_bot_id)
        try:
            message_processor = MessageProcessor(sender_id, bot, channel, message, data_manager)
        except Exception as e:
            logger.error(f"[ERROR][check_message] {e}")
            return
        await message_processor.run()
        subscribers = await data_manager.get_channel_subscribers(channel_id)
        for subscriber in subscribers:
            subscriber_id = subscriber.get("id")
            if subscriber_id != default_bot_id:
                bot = await data_manager.get_bot(subscriber_id)
                try:
                    message_processor = MessageProcessor(sender_id, bot, channel, message, data_manager)
                except Exception as e:
                    logger.error(f"[ERROR][check_message] {e}")
                    return
                await message_processor.run()
        return True

    if recipient_id:
        bot = await data_manager.get_bot(recipient_id)
        if not bot:
            logger.warning("Bot not found.")
            return False
        try:
            message_processor = MessageProcessor(sender_id, bot, channel, message, data_manager)
        except Exception as e:
            logger.error(f"[ERROR][check_message] {e}")
            return
        await message_processor.run()
        return True
