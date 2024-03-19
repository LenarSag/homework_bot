class TokenNotFoundError(Exception):
    """Ошибка доступности токена в .env."""

    pass


class EndpointError(Exception):
    """Ошибка доступа к API Практикума."""

    pass


class ResponseNotValidError(Exception):
    """Ошибка при получении данных от API."""

    pass


class ResponseTypeError(TypeError):
    """Ошибка соответствия формата ответа документации."""

    pass


class MessageNotSentError(Exception):
    """Ошибка отправки сообщения."""

    pass


class HomeworkListEmptyError(IndexError):
    """Ошибка пустого листа домашнего заданию."""

    pass


class HomeworkVerdictError(Exception):
    """Ошибка отсутсвия информации о полученном статусе."""

    pass


class NetworkError(Exception):
    """Ошибка доступа сети."""

    pass
