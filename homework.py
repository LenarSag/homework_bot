import os
import sys
import logging
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
import telegram

from exceptions import TokenNotFoundError, PracticumAPINotAvailable, ResponseIsNotValid

load_dotenv()


PRACTICUM_TOKEN = os.getenv("YA_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELE_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("log.txt", encoding="UTF-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens(tokens_to_check):
    """Проверяем доступность переменных окружения, которые необходимы для работы программы."""
    for token in tokens_to_check:
        if token is None:
            logging.critical(f"Отсутствует обязательная переменная окружения: {token}")
            raise TokenNotFoundError


def send_message(bot, message):
    pass


def get_api_answer(timestamp):
    """Получаем статус домашней работы."""
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
        status_code = homework_statuses.status_code
        if status_code != HTTPStatus.OK:
            # logging.error(
            #     f"Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. Код ответа API: {status_code}"
            # )
            raise PracticumAPINotAvailable(
                f"Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. Код ответа API: {status_code}"
            )
        return homework_statuses.json()
    except Exception:
        raise ConnectionError


def check_response(): ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    check_tokens(tokens)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    current_status = {"homework_name": "", "verdict": ""}
    prev_status = current_status.copy()

    while True:
        try:
            get_api_answer(timestamp)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            ...
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
