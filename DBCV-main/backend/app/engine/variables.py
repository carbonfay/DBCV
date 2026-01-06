import json
import logging
from typing import Any, Dict, List, Union, Optional, Tuple, Type
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SessionModel
from app.models.base import BaseModel
from pydantic import BaseModel as BaseModelPydantic
import app.crud.variables as crud_variables
from app.models import BotVariables, UserVariables, ChannelVariables, SessionVariables
import re
from app.utils.dict import deep_merge_dicts, get_value_by_list_keys
from app.crud.attachment import create_attachment
from app.engine.files import create_universal_file_attachment
from fastapi import UploadFile
import io
from functools import lru_cache

# Compile Regex
VARIABLE_PATTERN = re.compile(r'\{\$([a-zA-Z0-9._|]+)\$}')


async def variable_loader(
                          variable_name: str,
                          context: Dict[str, Any] | None = None) -> Any:
    """
    Загружает значение переменной.
    Сначала пытается получить значение из контекста, если он предоставлен.
    В противном случае читает переменную из базы данных.
    """
    value = None
    if context:
        value = get_value_by_list_keys(context, variable_name.split("."))
    return value


async def replace_variables_universal(
        data: Union[str, List[Any], Dict[str, Any]] = {},
        context: Dict[str, Any] | None = None
) -> Union[str, List[Any], Dict[str, Any]]:
    """
    Рекурсивно заменяет переменные в формате {$variable_name$} в строке, списке или словаре
    на соответствующие значения, полученные с помощью функции variable_loader.
    """

    def replace_in_string(text: str, replacements: Dict[str, Any]) -> str:
        """
        Заменяет переменные в строке, используя предоставленные значения.
        """

        def replace_match(match: re.Match) -> str:
            """
            Внутренняя функция для обработки одного совпадения переменной.
            """
            variable_name = match.group(1)
            # Ensure the value is JSON encoded only if it's not a primitive or collection type
            value = replacements[variable_name]
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)  # Encode for complex types
            else:
                if value is None:
                    return ""
                return str(value)  # Ensure it is still represented as string in the target data

        return VARIABLE_PATTERN.sub(replace_match, text)  # Returns origin Type

    if isinstance(data, str):
        # 1. Extract replace map
        variable_names = extract_variable_names(data)  # Extract map to go through.
        if variable_names:
            replacements: Dict[str, Any] = {}
            for variable_name in variable_names:  # Go through variable names
                value = await variable_loader(variable_name, context)  # Load values from variable loader, Passing context
                replacements[variable_name] = value

            new_string = replace_in_string(data, replacements)  # Returns origin Type
            # Now we attempt to convert this to JSON or leave it be

            if isinstance(new_string, str):  # This is only done IF new Type == str
                try:
                    return json.loads(new_string)  # Try to get back a JSON if you can
                except json.JSONDecodeError as e:
                    return new_string  # return String if cant
            else:
                return new_string  # We have JSON - no need to string it.
        return data  # Return data if No variables where found!

    elif isinstance(data, list):
        new_list: List[Any] = []
        for item in data:
            # Рекурсивно обрабатываем каждый элемент списка.
            new_list.append(
                await replace_variables_universal(item, context))
        return new_list

    elif isinstance(data, dict):
        new_dict: Dict[str, Any] = {}
        for key, value in data.items():
            # Process Key
            new_key = key
            if isinstance(key, str):
                # Рекурсивно обрабатываем ключ, если он строка.
                new_key = await replace_variables_universal(key, context)

            # Рекурсивно обрабатываем значение.
            new_dict[new_key] = await replace_variables_universal(value, context)

        return new_dict

    return data


def extract_variable_names(text: str) -> Optional[List[str]]:
    """
    Извлекает имена переменных из строки, используя регулярное выражение.
    """
    matches = VARIABLE_PATTERN.findall(text)
    return list(set(matches)) if matches else None


async def variable_substitution(
        data: Union[str, List[Any], Dict[str, Any]],
        context: Dict[str, Any] | None = None) -> str:
    """
    Выполняет подстановку переменных в данных.
    Если входные данные - строка, пытается преобразовать ее в JSON.
    Вызывает replace_variables_universal для выполнения подстановки.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass
    data = await replace_variables_universal(data, context)
    if isinstance(data, (dict, list)):
        try:
            data = json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    return data


def get_variable_pks(session_obj: SessionModel,
                     cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables) -> tuple[str]:
    """
    Возвращает кортеж первичных ключей для заданной переменной.
    """

    if cls_variables == BotVariables:
        return (str(session_obj.bot_id),)
    if cls_variables == UserVariables:
        return (str(session_obj.user_id),)
    if cls_variables == ChannelVariables:
        return (str(session_obj.channel_id),)
    if cls_variables == SessionVariables:
        return (str(session_obj.id),)


@lru_cache(maxsize=128)  # Кэшируем результаты, если вызовы частые
def get_variable_cls(namespace: str) -> Optional[Type[BaseModel]]:
    """
    Получает класс переменной по пространству имен.
    """
    for mapper in BaseModel.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ == f"{namespace}_variables":
            return cls
    return None


def split_namespace(variable: str) -> Tuple[str, List[str]]:
    """
    Разделяет имя переменной на пространство имен и части переменной.
    """
    namespace, *variable_parts = variable.split(".")
    return namespace, variable_parts


def split_list_mode(name_variable: str) -> Tuple[str, Optional[str]]:
    """
    Разделяет имя переменной на имя и режим (например, "a" для добавления).
    """
    name_variable, *mode = name_variable.split("|")
    return name_variable, mode[0] if mode else None


def split_file_ext(name_variable: str) -> Tuple[str, Optional[str]]:
    """
    Разделяет имя переменной на имя и расширение файла (если есть).
    """
    name_variable, *ext = name_variable.split("|file|")
    return name_variable, ext[0] if ext else None


async def create_file_attachment(session: AsyncSession, data: Any, ext: str) -> Dict[str, Any]:
    """
    Создает вложение файла из данных.
    """
    b = io.BytesIO(bytes(data, encoding='utf-8'))
    file = UploadFile(file=b, size=0, filename=f"file{ext}")
    attachment = await create_attachment(session, file)
    await session.commit()
    await session.refresh(attachment)
    return attachment.get_dict()


def create_variable_dict(variable_parts: list, value: Any) -> dict:
    """
    Создает вложенный словарь на основе списка ключей и значения.
    """
    if not variable_parts:
        return value

    return {variable_parts[0]: create_variable_dict(variable_parts[1:], value)}


async def get_variable_by_cls(session: AsyncSession, session_obj: SessionModel, variable_cls) -> Any:
    """
    Получает переменную по классу переменной.
    """
    variable_pks = get_variable_pks(session_obj, variable_cls)
    return await crud_variables.get_variable_by_pks(session, variable_cls, variable_pks)


async def get_variable_by_namespace(session: AsyncSession, session_obj: SessionModel, namespace: str) -> Any:
    """
    Получает переменную по пространству имен.
    """
    variable_cls = get_variable_cls(namespace)
    if not variable_cls:
        raise ValueError(f"Неизвестное пространство имен: {namespace}")
    return await get_variable_by_cls(session, session_obj, variable_cls)


async def read_variable(session: AsyncSession, session_obj: SessionModel, name_variable: str) -> str:
    """
    Читает значение переменной из базы данных.
    """
    namespace, variable_parts = split_namespace(name_variable)
    variable = await get_variable_by_namespace(session, session_obj, namespace)
    return get_value_by_list_keys(variable.get_data(), variable_parts)


async def _handle_file_attachment(session: AsyncSession, value: Any, ext: str) -> Dict[str, Any]:
    """Обрабатывает сохранение в файл."""
    file_type = ext.split(".")[1]
    return await create_universal_file_attachment(session, value, file_type)


async def _handle_list_mode(session: AsyncSession, session_obj: SessionModel, target_variable_path: str,
                            mode: Optional[str], value: Any) -> Any:
    """Обрабатывает добавление в список (режим "a")."""
    match mode:
        case "a":
            namespace, variable_parts = split_namespace(target_variable_path)
            variable_cls = get_variable_cls(namespace)
            if not variable_cls:
                raise ValueError(f"Неизвестное пространство имен: {namespace}")
            variable_pks = get_variable_pks(session_obj, variable_cls)
            variable_obj = await crud_variables.get_variable_by_pks(session, variable_cls, variable_pks)
            old_value = get_value_by_list_keys(variable_obj.get_data(), variable_parts) if variable_obj else None
            # Объединяем старое и новое значения
            if old_value is not None:
                value = old_value + value
    return value


def _build_variable_dict(variable_parts: List[str], value: Any) -> Dict[str, Any]:
    """Создает вложенный словарь для сохранения переменной."""
    return create_variable_dict(variable_parts, value)


async def _save_namespace_data(session: AsyncSession,
                               session_obj: SessionModel,
                               namespace: str,
                               data_to_save: Dict[str, Any]) -> None:
    """Сохраняет данные для одного пространства имен."""
    variable_cls = get_variable_cls(namespace)
    if variable_cls:
        variable_pks = get_variable_pks(session_obj, variable_cls)
        await crud_variables.update_variable_by_pks(session, variable_cls, variable_pks, data_to_save)
    else:
        logging.warning(f"Неизвестное пространство имен: {namespace}. Данные не сохранены.")


async def _process_variable(session: AsyncSession,
                            session_obj: SessionModel,
                            source_path: str,
                            target_path: str,
                            context: Dict[str, Any]) -> Union[Tuple[str, Any], Tuple[None, None]]:
    """Обрабатывает одну переменную: подстановка, обработка режимов."""
    # Подставляем переменные
    source_path = await variable_substitution(source_path, context)
    target_path = await variable_substitution(target_path, context)

    # Получаем значение из context
    source_parts = source_path.split(".")
    value = get_value_by_list_keys(context, source_parts)

    if value is None:
        return None, None  # Пропускаем, если значение не найдено

    # Обработка сохранения в файл
    target_variable_path, ext = split_file_ext(target_path)
    if ext:
        value = await _handle_file_attachment(session, value, ext)
    else:
        # Обработка добавления в список
        target_variable_path, mode = split_list_mode(target_path)
        value = await _handle_list_mode(session, session_obj, target_variable_path, mode, value)
    return target_variable_path, value


async def save_variables(session: AsyncSession,
                         session_obj: SessionModel,
                         variables: Dict[str, str],
                         context: Dict[str, Any]) -> None:
    """
    Сохраняет несколько переменных в базе данных, используя подстановку переменных.
    """
    all_data: Dict[str, Dict[str, Any]] = {}

    for source_path, target_path in variables.items():
        try:
            target_variable_path, value = await _process_variable(session, session_obj, source_path, target_path,
                                                                  context)

            if value is None:
                continue  # Пропускаем переменную, если нет значения

            namespace, variable_parts = split_namespace(target_variable_path)
            variable_dict = _build_variable_dict(variable_parts, value)
            all_data[namespace] = deep_merge_dicts(all_data.get(namespace, {}), variable_dict)

        except Exception as e:
            logging.exception(f"Ошибка при обработке переменной {source_path} -> {target_path}: {e}")
    for namespace, data_to_save in all_data.items():
        try:
            await _save_namespace_data(session, session_obj, namespace, data_to_save)
        except Exception as e:
            logging.exception(f"Ошибка при сохранении данных для пространства имен {namespace}: {e}")


async def get_all_variables_dict(session: AsyncSession, session_obj: SessionModel) -> Dict[
    str, Optional[Dict[str, Any]]]:
    """
    Получает словарь со всеми переменными для заданного объекта сессии.
    """

    variable_types: Dict[str, Type[BaseModel]] = {
        "bot": BotVariables,
        "session": SessionVariables,
        "user": UserVariables,
        "channel": ChannelVariables,
    }

    variables_dict: Dict[str, Optional[Dict[str, Any]]] = {}

    for name, var_type in variable_types.items():
        variable = await get_variable_by_cls(session, session_obj, var_type)
        variables_dict[name] = variable.get_data() if variable else None

    return variables_dict


async def variable_substitution_pydantic(
                                         model: Type[BaseModelPydantic],
                                         context: Dict[str, Any] | None = None) -> BaseModel:
    """
    Выполняет подстановку переменных в полях Pydantic-модели.
    """
    data = await replace_variables_universal(model.model_dump(), context)
    return model.model_validate(data)


async def update_variables_dict(current_vars: dict,
                                 session: AsyncSession,
                                 variables: dict,
                                 context: dict) -> dict:
    updated_vars = current_vars.copy()
    for source_path, target_path in variables.items():
        target_variable_path, value = await _process_variable(session, session, source_path, target_path, context)
        if value is None:
            continue
        namespace, variable_parts = split_namespace(target_variable_path)
        variable_dict = _build_variable_dict(variable_parts, value)
        updated_vars[namespace] = deep_merge_dicts(updated_vars.get(namespace, {}), variable_dict)
    return updated_vars
