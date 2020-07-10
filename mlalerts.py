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


def load_search(filename: str):
    filename = config.SEARCH_DIRECTORY + filename
    try:
        return pickle.load(open(filename, 'rb'))
    except:
        return None

def dump_search(filename: str, search: dict):
    if not os.path.exists(config.SEARCH_DIRECTORY):
        os.mkdir(config.SEARCH_DIRECTORY)
    pickle.dump(search, open(config.SEARCH_DIRECTORY + filename, 'wb'))

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
    if not os.path.exists('searches'):
        os.mkdir('searches')
    saved_searches = os.listdir('searches')
    if len(saved_searches) == 0:
        print('No previous search done - Go back and query something using --query!')
        return None
    while True:
        i = 0
        for filename in saved_searches:
            search = load_search(filename)
            data = __get(search)
            pending_results = data['paging']['total'] - len(search['ids'])
            print('[{}] - {} - ({})'.format(i, search['query'], pending_results))
            i += 1
        numero_valor = input_numero('>> ', len(saved_searches))

        if numero_valor is None:
            sys.exit()
        query = saved_searches[numero_valor].split('.')[0]
        break
    return query

def interactive_mode(query: str) -> None:
    if not query:
        query = select_query()
    pickle_filename = query.replace(' ', '_') + '.pickle'
    search = load_search(pickle_filename)
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
            print()
            descartar = input('Descartar? [S/n] q to exit >> ')
            if descartar.lower() == 'q':
                break
            if descartar.lower() != 'n':
                search['ids'].add(item['id'])
            i += 1
        if descartar.lower() == 'q':
            break
    dump_search(pickle_filename, search)
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
    pickle_list = []
    email = config.get('EMAIL_USERNAME')
    password = config.get('EMAIL_PASS')
    if query:
        pickle_filename = query.replace(' ', '_') + '.pickle'
        if not os.path.exists(config.SEARCH_DIRECTORY + pickle_filename):
            print('Invalid search:', query)
            return
        pickle_list.append(pickle_filename)
    else:
        pickle_list = os.listdir(config.SEARCH_DIRECTORY)

    if len(pickle_list) == 0:
        print('ERROR - No saved searches to alert you on... GO DO SOME SEARCH!')
        return
    for pickle_filename in pickle_list:
        search = load_search(pickle_filename)
        data = __get(search)
        pending_results = data['paging']['total'] - len(search['ids'])
        if pending_results > 0:
            print('Enviamos una ALERT - {} new results for {}'.format(
                pending_results, search['query']))
            message = 'Hay {} resultados nuevos para revisar para la busqueda "{}"'.format(pending_results, search['query'])
            send_mail(message)
        else:
            print('Nada nuevo para esta search')

def del_query():
    print('Choose file to delete - WARNING ACTION CAN\'T BE UNDONE')
    pickle_filename = select_query() + '.pickle'
    os.remove(config.SEARCH_DIRECTORY + pickle_filename)
    print('Done!')
    return

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '-a':
        query = ' '.join(sys.argv[2:]).lower()
        alert_mode(query)
    elif len(sys.argv) > 1 and sys.argv[1] == '-d':
        del_query()
    else:
        query = ' '.join(sys.argv[1:]).lower()
        interactive_mode(query)

#TODO

# tiene sentido usar archivos pickle distintos ??? PENSAR! LATIGO !!! LATIGO!!!
# Me parece o creo que podriamos usar un diccionario que contenga las busquedas
# puedo hacer con un archivo que contenga clave 'query': el dict de la busqueda
