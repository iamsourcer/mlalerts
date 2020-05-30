#!/usr/bin/python3

import json
import math
import pickle
import requests


def load_search(filename):
    try:
        return pickle.load(open(filename, 'rb'))
    except:
        return None

# TODO: pasar como parametro con search y parametro page en ves de offset
def __get(URL, q, offset=0, filter=None):
    url = URL.format(q, offset)
    if filter:
        url += '&{}={}'.format(filter['filtro_id'], filter['valor_id'])
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def select_filter(filtros):
    i = 0
    for filtro in filtros:
        print('[{}] - {}'.format(i, filtro['name']))
        i += 1
    numero_filtro = int(input('>>> '))
    filtro = filtros[numero_filtro]

    i = 0
    values = filtro['values']
    for value in values:
        print('[{}] {} - ({})'.format(i, value['name'], value['results']))
        i += 1
    numero_valor = int(input('>>> '))
    valor = values[numero_valor]
    return  {'filtro_id': filtro['id'], 'valor_id': valor['id']}


if __name__ == '__main__':

    FILNAME = 'mlalerts.pickle'
    BASE_URL = 'https://api.mercadolibre.com'
    ENDPOINT = '/sites/MLA/search'
    URL = BASE_URL + ENDPOINT + '?q={}&offset={}'

    search = load_search(FILNAME)
    if search == None:
        q = input('Que queres buscar >>> ')
        data = __get(URL, q)
        available_filters = data['available_filters']
        filtro  = select_filter(available_filters)
        search = {'query': q,
                  'filter': filtro,
                  'ids': set()}

    # En este punto ya vamos a revisar las publicaciones

    data = __get(URL, search['query'], 0, search['filter'])
    total_pages = math.ceil(data['paging']['total'] / 50)
    offset = 0
    i = 0
    for page in range(total_pages):
        for item in data['results']:
            if item['id'] in search['ids']:
                continue
            print()
            print(i, '.', item['title'])
            print('$', item['price'])
            print()
            # TODO: agregar la salida
            descartar = input('Descartar? [S/n]')
            if descartar.lower() != 'n':
                search['ids'].add(item['id'])
            i += 1
        offset += 50
        data = __get(URL, search['query'], offset, search['filter'])

    pickle.dump(search, open('mlalerts.pickle', 'wb'))


# TODO
# poder aplicar mas de un filtro

