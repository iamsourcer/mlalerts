#!/usr/bin/python3

import json
import math
import sys
import requests
import config
from background_jobs import alert_mode, __get


def get_search(query: str) -> dict:
    ''' loads a specific search '''

    url = config.API_BASE_URL + '/' + query
    response = requests.get(url)

    if response.status_code != 200:
        return None
    search = json.loads(response.text)
    return search

def get_searches() -> list:
    ''' Loads all saved searches from our server '''

    url = config.API_BASE_URL
    response = requests.get(url)
    searches = json.loads(response.text)
    return searches

def create_search(search: dict):
    ''' PUT/POST en nuestra API'''

    headers = {'Content-Type': 'application/json'}
    search['ids'] = list(search['ids'])
   # vamos a tener que determinar si la busqueda YA existe o si es una busqueda nueva a dumpear y de ahi el metodo a usar
    requests.post(config.API_BASE_URL, data=json.dumps(search), headers=headers)


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
    ''' Esta funcion toma los filtros de la API de MELI '''

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
    ''' Selects query from list of queries '''

    searches = get_searches()
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
    search = get_search(query) # de ahora en mas get_search va a hacer un GET al endpoint API/searches/query
    if search is  None:
        search = select_filters(query)
    # En este punto ya vamos a revisar las publicaciones
    data = __get(search) # get esta llamando a nuestra OTRA API - mercadolibre con los datos que obtenemos de client.py
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
                search['ids'].append(item['id'])
            i += 1
        if descartar.lower() == 'q':
            break
    create_search(search) # vamos a utilizar server.py para hacer el dump
    return

def del_query(query: str) -> bool:
    ''' This function deletes a selected query'''

    if not query:
        return False

    response = requests.delete(config.API_BASE_URL + '/' +  query)
    if response.status_code == 200:
        print('Done!')
        return True

    print(response.status_code, 'ERROR - can\'t  delete')
    return False

def reset_query(query: str):
    ''' This function resets query filters '''

    search = select_filters(query)
    update_search(search)
    #create_search(search) # hacemos un PUT al server dado  que la query ya existe

def update_search(search):
    query = search['query']
    headers = {'Content-Type': 'application/json'}
    search['ids'] = list(search['ids'])
    response  = requests.put(config.API_BASE_URL + '/' +  query, data=json.dumps(search), headers=headers)
    return response


if  __name__ == '__main__':

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




