#!/usr/bin/python3

# Telegram API token

TELEGRAM_API_TOKEN = '1266507409:AAGiGezj0bAdpyZ6LtCzWqaxCU6Jv3FUNbY'

# Email account info

EMAIL_USERNAME = ''
EMAIL_PASS = ''

# API config

API_BASE_URL = 'http://127.0.0.1:5000/searches'
# Main config

LIMIT = 49
BASE_URL = 'https://api.mercadolibre.com'
ENDPOINT = '/sites/MLA/search'
URL = BASE_URL + ENDPOINT + '?q={}&offset={}'
PICKLE_FILENAME = 'database.pickle'


def get(parameter: str):
    try:
        return eval(parameter)
    except Exception as e:
        print(f'ERROR - parameter {parameter} not defined - check config.py')
        raise e
