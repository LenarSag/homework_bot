class TokenNotFoundError(Exception):
    """Ошибка доступности токена в .env."""

    pass


class PracticumAPINotAvailable(Exception):
    """Ошибка доступа к API Практикума."""

    pass


class ResponseIsNotValid(Exception):
    """Ошибка соответствия формата ответа документации."""

    pass
