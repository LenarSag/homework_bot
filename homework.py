import os
import sys
import logging
import time
from http import HTTPStatus
from typing import Union

import requests
from dotenv import load_dotenv
import telegram

import exceptions


load_dotenv()

PRACTICUM_TOKEN = os.getenv("YA_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELE_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


logger = logging.getLogger(__name__)

logging.basicConfig(
    format=(
        "%(filename)s:%(lineno)d #%(levelname)s "
        "[%(asctime)s] - %(name)s - %(message)s"
    ),
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("log.txt", encoding="UTF-8", mode='w'),
        logging.StreamHandler(sys.stdout),
    ],
)


def check_tokens(tokens_to_check: dict[str, Union[str, None]]) -> None:
    """Проверяем переменные окружения, необходимыe для работы программы."""
    for token, token_value in tokens_to_check.items():
        if token_value is None:
            logging.critical(
                "Отсутствует обязательная переменная "
                f"{token.upper()} окружения"
            )
            raise exceptions.TokenNotFoundError(
                "Отсутствует обязательная переменная "
                f"{token.upper()} окружения"
            )


def send_message(bot, message):
    """Отправка статус домашней работы либо ошибки в телеграмм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f"Сообщение {message} успешно отправлено!")
    except Exception as error:
        raise exceptions.MessageNotSentError(
            f"При отправке сообщения в телеграм произошла ошибка: {error}"
        )


def get_api_answer(timestamp):
    """Получаем статус домашней работы."""
    payload = {"from_date": timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        status_code = homework_statuses.status_code
        if status_code != HTTPStatus.OK:
            raise exceptions.EndpointError(
                f"Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен."
                f"Код ответа API: {status_code}"
            )
        try:
            return homework_statuses.json()
        except requests.exceptions.InvalidJSONError as error:
            raise exceptions.ResponseTypeError(
                f"Невалидный формат JSON от API {error}"
            )
    except requests.exceptions.RequestException as error:
        raise exceptions.NetworkError(f"Проблемы с соединением, {error}")


def check_response(response):
    """Проверка валидности данных полученных от API."""
    if not isinstance(response, dict):
        raise exceptions.ResponseTypeError("Ответ должен быть в формате dict")

    if "code" in response:
        code = response.get("code")
        message = response.get("message")
        raise exceptions.ResponseNotValidError(
            f"В ответе API содержится сообщение об ошибке {code} "
            f"с текстом {message}"
        )

    homeworks = response.get("homeworks")
    if homeworks is None:
        raise exceptions.ResponseNotValidError(
            "В ответе API отсутствуют данные по ключу 'homewokrs'"
        )

    if not isinstance(homeworks, list):
        raise exceptions.ResponseTypeError(
            "Ключ 'homeworks' должен быть списком"
        )

    if homeworks:
        return homeworks[0]
    raise exceptions.HomeworkListEmptyError(
        "За указанный период данные не найдены"
    )


def parse_status(homework):
    """Проверка статуса домашнего задания."""
    if not isinstance(homework, dict):
        raise exceptions.ResponseTypeError(
            "Переменная 'homework' должна быть в формате dict"
        )

    homework_name = homework.get("homework_name")
    if homework_name is None:
        raise exceptions.ResponseTypeError("Отсутствует ключ 'homework_name'")

    homework_status = homework.get("status")
    if homework_status is None:
        raise exceptions.ResponseTypeError(
            "Отсутствует ключ 'homework_status'"
        )
    if homework_status not in HOMEWORK_VERDICTS.keys():
        raise exceptions.HomeworkVerdictError(
            "Неожиданный статус домашней работы, полученный в ответе API"
        )
    verdict = HOMEWORK_VERDICTS.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    tokens = {
        "practikum_token": PRACTICUM_TOKEN,
        "telegram_token": TELEGRAM_TOKEN,
        "telegram_chat_id": TELEGRAM_CHAT_ID,
    }
    check_tokens(tokens)

    prev_status = None

    current_alarm = None
    prev_alarm = None

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homework_info = check_response(response)
            message = parse_status(homework_info)

            if message != prev_status:
                prev_status = message
                send_message(bot, message)

        except exceptions.MessageNotSentError:
            logging.error("Сбой при отправке сообщения в Telegram")

        except exceptions.HomeworkListEmptyError as error:
            logging.debug(f"{error}")

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            current_alarm = message
            if current_alarm != prev_alarm:
                prev_alarm = current_alarm
                send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
