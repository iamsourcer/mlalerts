#!/usr/bin/python3

import json
import math
import pickle
import sys
import os
from os import path
import requests
import yagmail
import config


def load_search(query: str) -> dict:
    filename = config.get('PICKLE_FILENAME')
    try:
        searches = pickle.load(open(filename, 'rb'))
        return searches[query]
    except:
        return None

def load_searches() -> list:
    filename = config.get('PICKLE_FILENAME')
    try:
        searches = pickle.load(open(filename, 'rb'))
        return list(searches,values())
    except:
        return None

def dump_search(search: dict):
    filename = config.get('PICKLE_FILENAME')
    try:
        searches = pickle.load(open(filename, 'rb'))
        searches[search['query']] = search
    except:
        searches = {search['query']: search}
    pickle.dump(searches, open(config.get('PICKLE_FILENAME'), 'wb'))

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

def es_numero(string: str, maximo: int) -> bool:
    if not string.isdigit():
        return False
    if not int(string) in range(0, maximo):
        return False
    return True

def input_numero(prompt: str, maximo: int) -> int:
    entrada = input(prompt)
    if not entrada:
        return None
    while not es_numero(entrada, maximo):
        entrada = input(prompt)
        if not entrada:
            return None
    return int(entrada)

def select_filters(q: str) -> dict:
    search = {
        'query': q,
        'filters': [],
        'ids': set(),
        }

    while True:
        i = 0
        data = __get(search)
        filtros = data['available_filters']
        total_results = data['paging']['total']
        print('Total listings:', total_results)

        for filtro in filtros:
            print('[{}] - {}'.format(i, filtro['name']))
            i += 1
        numero_filtro = input_numero('>> ', len(filtros))

        if numero_filtro is None:
            break

        filtro = filtros[int(numero_filtro)]
        i = 0
        values = filtro['values']
        for value in values:
            print('\t[{}] {} - ({})'.format(i, value['name'], value['results']))
            i += 1
        numero_valor = input_numero('\t>> ', len(values))
        if numero_valor is not  None:
            valor = values[numero_valor]
            search['filters'].append({'filtro_id': filtro['id'], 'valor_id': valor['id']})
    return search

def select_query() -> str:
    filename = config.get('PICKLE_FILENAME')
    searches = load_searches()
    if len(searches) == 0:
        print('No previous search done - Go back and query something using --query!')
        return None
    while True:
        i = 0
        for search in searches:
            data = __get(search)
            pending_results = data['paging']['total'] - len(search['ids'])
            print('[{}] - {} - ({})'.format(i, search['query'], pending_results))
            i += 1
        numero_valor = input_numero('>> ', len(searches))

        if numero_valor is None:
            sys.exit()
        query = searches[numero_valor]['query']
        break
    return query

def interactive_mode(query: str) -> None:
    if not query:
        query = select_query()
    search = load_search(query)
    if search is  None:
        search = select_filters(query)
    # En este punto ya vamos a revisar las publicaciones
    data = __get(search)
    total_pages = math.ceil(data['paging']['total'] / config.LIMIT)
    pending_results = data['paging']['total'] - len(search['ids'])
    print('total listings:', pending_results)
    i = 0
    for page in range(total_pages):
        data = __get(search, page)
        descartar = ''
        for item in data['results']:
            if item['id'] in search['ids']:
                continue
            print()
            print(i, '.', item['title'])
            print('$', item['price'])
            print('Link: ', item['permalink'])
            print()
            descartar = input('Descartar? [S/n] q to exit >> ')
            if descartar.lower() == 'q':
                break
            if descartar.lower() != 'n':
                search['ids'].add(item['id'])
            i += 1
        if descartar.lower() == 'q':
            break
    dump_search(search)
    return

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
            print('Enviamos una ALERT - {} new results for {}'.format(
                pending_results, search['query']))
            message = 'Hay {} resultados nuevos para revisar para la busqueda "{}"'.format(pending_results, search['query'])
            send_mail(message)
        else:
            print('Nada nuevo para esta search')

def del_query(query):
    ''' This function deletes a selected query'''

    filename = config.get('PICKLE_FILENAME')
    searches = pickle.load(open(filename, 'rb'))

    print('Choose file to delete - WARNING ACTION CAN\'T BE UNDONE')
    if query != '' :
        print(query)
        searches.pop(query, None)
        dump_search(searches)
        print('Done!')
        return
    while True:
        i = 0
        for search in searches:
            print('[{}] - {}'.format(i, search))
            i += 1

        numero_valor = input_numero('>> ', len(searches))

        if numero_valor is None:
            sys.exit()
    return

def reset_query(query: str):
    ''' This function resets query filters '''

    search = select_filters(query)
    dump_search(search)
    interactive_mode(query)


if __name__ == '__main__':

    opciones = {
        'alert' : ['-a', '--alert', '-alert', '-alerts', '--alerts'],
        'reset' : ['-r', '--reset', '-reset'],
        'delete' : ['-d', '--delete', '-delete']
    }

    if len(sys.argv) > 1 and sys.argv[1] in opciones['alert']:
        query = ' '.join(sys.argv[2:]).lower()
        alert_mode(query)
    elif len(sys.argv) > 1 and sys.argv[1] in opciones['delete']:
        query = ' '.join(sys.argv[2:]).lower()
        del_query(query)
    elif len(sys.argv) > 1 and  sys.argv[1] in opciones['reset']:
        query = ' '.join(sys.argv[2:]).lower()
        reset_query(query)
    else:
        query = ' '.join(sys.argv[1:]).lower()
        interactive_mode(query)

#TODO

# API para el pickle de las busquedas

# GET api/searches?q=query para devolver una busqueda especifica
# GET api/searches --> json con un array con cada busqueda
# POST api/searches --> agrega una busqueda al pickle
# DELETE api/searches --> borramos una buqueda
# PUT api/searches --> updateamos una busqueda

