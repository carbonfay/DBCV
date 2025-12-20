"""Local pytest stub to satisfy static analysis."""

from typing import Any, Callable, TypeVar

_Func = TypeVar("_Func", bound=Callable[..., Any])


def fixture(func: _Func, /, *args: Any, **kwargs: Any) -> _Func: ...


class _MarkDecorator:
    def __call__(self, func: _Func, /, *args: Any, **kwargs: Any) -> _Func: ...


class mark:
    asyncio: _MarkDecorator
