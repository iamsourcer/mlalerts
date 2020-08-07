#!/usr/bin/python3

''' This module hanldes all background jobs for mlalerts '''


import requests
import json
import pickle
import yagmail
import config


def __get(search, page=0):
    if isinstance(search, str):
        q = search
        filters = None
    else:
        q = search['query']
        filters = search['filters']

    offset = page * config.LIMIT
    url = config.URL.format(q, offset)
    if filters:
        for d in filters:
            url += '&{}={}'.format(d['filtro_id'], d['valor_id'])
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def send_mail(message: str) -> None:
    ''' function used to send email alert '''

    try:
        yag = yagmail.SMTP(user=config.EMAIL_USERNAME, password=config.EMAIL_PASS)
        yag.send(to=config.EMAIL_USERNAME,
              subject='MLAlerts', contents=message)
        print('Email Sent!')
    except:
        print('ERROR!, unvaible to send email, check username or password in config file')
    return

def alert_mode(query: str):
    ''' function that handles all alerts '''

    email = config.get('EMAIL_USERNAME')
    password = config.get('EMAIL_PASS')
    filename = config.get('PICKLE_FILENAME')
    searches = pickle.load(open(filename, 'rb'))
    active_searches = []

    if query:
        if not query in searches.keys():
            print('Invalid search:', query)
            return
        active_searches.append(searches[query])
    else:
        active_searches = searches.values()

    if len(active_searches) == 0:
        print('ERROR - No saved searches to alert you on... GO DO SOME SEARCH!')
        return

    for search in active_searches:
        data = __get(search)
        pending_results = data['paging']['total'] - len(search['ids'])
        if pending_results > 0:
            print('ALERT sent - {} new results for {}'.format(
                pending_results, search['query']))
            message = 'Found {} new results to review for search -> "{}"'.format(pending_results, search['query'])
            send_mail(message)
        else:
            print('Nothing new for this search')
