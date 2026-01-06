from fastapi import status, HTTPException


class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек")


class TokenNoFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не найден")


UserAlreadyExistsException = HTTPException(status_code=status.HTTP_409_CONFLICT,
                                           detail='Пользователь уже существует')

UserInactiveException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user.")

PasswordMismatchException = HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Пароли не совпадают!')

IncorrectEmailOrPasswordException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                  detail='Неверная почта или пароль')

IncorrectUsernameOrPasswordException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                  detail='Неверный логин или пароль')

NoJwtException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                               detail='Токен не валидный!')

NoUserIdException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                  detail='Не найден ID пользователя')

ForbiddenException = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')


class ApiException(Exception):
    """
    This class represents a base Exception thrown when a call to the Telegram API fails.
    In addition to an informative message, it has a `function_name` and a `result` attribute, which respectively
    contain the name of the failed function and the returned result that made the function to be considered  as
    failed.
    """

    def __init__(self, msg, result):
        super(ApiException, self).__init__("A request to the Telegram API was unsuccessful. {0}".format(msg))
        self.result = result


class ApiHTTPException(ApiException):
    """
    This class represents an Exception thrown when a call to the
    Telegram API server returns HTTP code that is not 200.
    """
    def __init__(self, result):
        super(ApiHTTPException, self).__init__(
            "The server returned HTTP {0}. Response body:\n[{1}]" \
            .format(result.status_code, result.reason, result.text.encode('utf8')),
            result)


class ApiInvalidJSONException(ApiException):
    """
    This class represents an Exception thrown when a call to the
    Telegram API server returns invalid json.
    """
    def __init__(self, result):
        super(ApiInvalidJSONException, self).__init__(
            "The server returned an invalid JSON response. Response body:\n[{0}]" \
            .format(result.text.encode('utf8')),
            result)