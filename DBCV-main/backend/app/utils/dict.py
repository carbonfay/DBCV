from typing import Any


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Рекурсивное слияние двух словарей."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def get_value_by_list_keys(obj: dict, keys: list) -> str | None:
    """
    Извлекает значение из вложенного словаря по списку ключей.
    Возвращает None, если ключ не найден.
    """
    try:
        value = obj
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return None


def set_variable_by_dot_path(data: dict, dot_path: str, value: Any) -> None:
    """
    Устанавливает значение в словарь по пути, разделённому точками.
    Пример:
        set_variable_by_dot_path(data, "foo.bar.baz", 123)
        → data = {"foo": {"bar": {"baz": 123}}}
    """
    keys = dot_path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def recursive_search_keys(data: dict, target_keys: set[str]) -> dict:
    """
    Рекурсивный поиск по вложенному JSON, ищет нужные ключи среди target_keys.
    Возвращает словарь {ключ: значение}.
    """
    found = {}

    def _search(obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in target_keys and k not in found:
                    found[k] = v
                _search(v)
        elif isinstance(obj, list):
            for item in obj:
                _search(item)

    _search(data)
    return found


def get_value_by_path(variables: dict, path: str | None) -> Any:
    """
    Получает значение из вложенного словаря по строке пути ("bot.number1").
    """
    if not path:
        return None
    keys = path.split(".")
    value = variables
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def deep_set(output: dict, path: str, value: Any) -> None:
    """
    Устанавливает значение в словарь по пути, создавая вложенность.
    """
    keys = path.split(".")
    current = output
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value