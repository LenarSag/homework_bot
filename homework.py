import os
import sys
import logging
import time
from http import HTTPStatus

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


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("log.txt", encoding="UTF-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def check_tokens(tokens_to_check):
    """Проверяем переменные окружения, необходимых для работы программы."""
    for token in tokens_to_check:
        if token is None:
            logging.critical("Отсутствует обязательная переменная окружения")
            raise exceptions.TokenNotFoundError(
                "Отсутствует обязательная переменная окружения"
            )


def send_message(bot, message):
    """Отправка статус домашней работы либо ошибки в телеграмм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f"Сообщение {message} успешно отправлено!")
    except Exception as error:
        raise exceptions.MessageNotSentError(f"{error}")


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
        return homework_statuses.json()
    except requests.exceptions.RequestException as error:
        raise exceptions.NetworkError(f"Проблемы с соединением, {error}")


def check_response(response):
    """Проверка валидности данных полученных от API."""
    if not isinstance(response, dict):
        raise exceptions.ResponseTypeError("Ответ должен быть в формате dict")

    if "code" in response:
        message = response.get("message")
        raise exceptions.ResponseNotValidError(f"{message}")

    homeworks = response.get("homeworks")
    if not isinstance(homeworks, list):
        raise exceptions.ResponseTypeError(
            "Ключ Homeworks должен быть списком"
        )
    try:
        return homeworks[0]
    except IndexError:
        raise exceptions.HomeworkListEmptyError(
            "За указанный период данные не найдены"
        )


def parse_status(homework):
    """Проверка статуса домашнего задания."""
    homework_name = homework.get("homework_name")
    if homework_name is None:
        raise exceptions.ResponseTypeError("Отсутствует ключ 'homework_name'")

    homework_status = homework.get("status")
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise exceptions.HomeworkVerdictError(
            "Неожиданный статус домашней работы, обнаруженный в ответе API"
        )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    check_tokens(tokens)

    current_status = None
    prev_status = None

    current_alarm = None
    prev_alarm = None

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        timestamp = int(time.time())
        try:
            response = get_api_answer(timestamp)
            homework_info = check_response(response)
            message = parse_status(homework_info)

            if message:
                current_status = message
                if current_status != prev_status:
                    prev_status = current_status
                    send_message(bot, message)
            else:
                logging.debug("Отсутствие в ответе новых статусов")

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
