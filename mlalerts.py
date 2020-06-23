#!/usr/bin/python3

import json
import math
import pickle
import requests
import argparse
import os

LIMIT = 50
SEARCH_DIRECTORY = 'searches/'
BASE_URL = 'https://api.mercadolibre.com'
ENDPOINT = '/sites/MLA/search'
URL = BASE_URL + ENDPOINT + '?q={}&offset={}'

def load_search(filename):
    try:
        return pickle.load(open(filename, 'rb'))
    except:
        return None

def __get(search, page=0):
    if isinstance(search, str):
        q = search
        filters = None
    else:
        q = search['query']
        filters = search['filters']

    offset = page * LIMIT
    url = URL.format(q, offset)
    if filters:
        for d in filters:
            url += '&{}={}'.format(d['filtro_id'], d['valor_id'])
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

def select_filters(q: str) -> dict:
    search = {
       'query': q,
       'filters': [],
       'ids': set()
        }

    while True:
        i = 0
        filtros = __get(search)['available_filters']

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
    saved_searches = os.listdir('searches')
    if not len(saved_searches) >= 1:
        print('No previous search done - Go back and query something!')
        return None
    print('Wanna Go back to these ??\n')
    while True:
        i = 0
        for search in saved_searches:
            print('[{}] - {}'.format(i, search))
            i += 1
        numero_valor = input_numero('>> ', len(saved_searches))

        if numero_valor is None:
            return None

        if numero_valor is not None:
            query = saved_searches[int(numero_valor)]
            break
    return query

def main(query):
    pickle_filename = query.replace(' ', '_') + '.pickle'
    pickle_filename = SEARCH_DIRECTORY + pickle_filename
    search = load_search(pickle_filename)
    if search is  None:
        search  = select_filters(query)
    # En este punto ya vamos a revisar las publicaciones
    data = __get(search)
    total_pages = math.ceil(data['paging']['total'] / LIMIT)
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
    pickle.dump(search, open(pickle_filename, 'wb'))

if __name__ == '__main__':

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--query',
                           help= 'query search')
    args = my_parser.parse_args()
    if args.query:
        main(args.query)
    else:
        query = select_query()
        if query is not None:
            main(query)

# TODO
# agregar un parametro como nombre del archivo pickle
# agregar parametro  para resetear la busqueda
# si uno ya tiene una busqueda en curso, me tendria que mostrar la cantidad de pub disponibles
# es decir la que me informa menos los IDS descartados [esas serian las nuevas pubs]
