#!/usr/bin/python3

import json
import math
import pickle
import requests


LIMIT = 50
FILENAME = 'mlalerts.pickle'
BASE_URL = 'https://api.mercadolibre.com'
ENDPOINT = '/sites/MLA/search'
URL = BASE_URL + ENDPOINT + '?q={}&offset={}'

def load_search(filename):
    try:
        return pickle.load(open(filename, 'rb'))
    except:
        return None

# TODO: flexibilizar la funcion __get para que tome un q: str o un search: dict
def __get(q=None, search=None, page=0, filter=None):
    offset = page * LIMIT
    if q:
        url = URL.format(q, offset)
        if filter:
            url += '&{}={}'.format(filter['filtro_id'], filter['valor_id'])
            print(url)
        response = requests.get(url)
        data = json.loads(response.text)
        return data
    q = search['query']
    url = URL.format(q, offset)
    if filter:
        url += '&{}={}'.format(filter['filtro_id'], filter['valor_id'])
        print(url)
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
    return int(entrada)

def select_filter(filtros: list) -> dict:
    i = 0
    for filtro in filtros:
        print('[{}] - {}'.format(i, filtro['name']))
        i += 1
    numero_filtro = input_numero('>> ', len(filtros))

    if not  numero_filtro:
        return None

    filtro = filtros[int(numero_filtro)]
    i = 0
    values = filtro['values']
    for value in values:
        print('[{}] {} - ({})'.format(i, value['name'], value['results']))
        i += 1
    numero_valor = int(input('>>> '))
    valor = values[numero_valor]
    return  {'filtro_id': filtro['id'], 'valor_id': valor['id']}

if __name__ == '__main__':
    search = load_search(FILENAME)
    if search == None:
        q = input('Que queres buscar >>> ')
        data = __get(q)
        available_filters = data['available_filters']
        filtro  = select_filter(available_filters)
        search = {'query': q,
                  'filter': filtro,
                  'ids': set()}
    # En este punto ya vamos a revisar las publicaciones
    # data = __get(search)

    data = __get(search['query'], page=0, filter=search['filter'])
    total_pages = math.ceil(data['paging']['total'] / LIMIT)
    # offset = 0
    i = 0
    for page in range(total_pages):
        # data = __get(search, page)
        data = __get(search['query'], page=page, filter=search['filter'])
        descartar = ''
        for item in data['results']:
            if item['id'] in search['ids']:
                continue
            print()
            print(i, '.', item['title'])
            print('$', item['price'])
            print()
            # TODO: agregar la salida
            descartar = input('Descartar? [S/n] q to exit')
            if descartar.lower() == 'q':
                break
            if descartar.lower() != 'n':
                search['ids'].add(item['id'])
            i += 1
        if descartar.lower() == 'q':
            break
        # offset += LIMIT
    pickle.dump(search, open(FILENAME, 'wb'))


# TODO
# Si no quiero aplicar filtro y apreto ENTER se rompe
# poder aplicar mas de un filtro

