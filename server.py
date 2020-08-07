
from flask import Flask, jsonify, abort, make_response, request
import pickle
import config

app = Flask(__name__)


def load_searches() -> dict:
    filename = config.get('PICKLE_FILENAME')
    searches = pickle.load(open(filename, 'rb'))
    for search in searches.values():
        search['ids'] = list(search['ids'])
    return searches

def dump_search(search: dict) -> dict:
    search_copy = search.copy()
    search_copy['ids'] = set(search_copy['ids'])
    searches = load_searches()
    searches[search_copy['query']] = search_copy
    filename = config.get('PICKLE_FILENAME')
    pickle.dump(searches, open(filename, 'wb'))


def dump_searches(searches: dict) -> dict:
    filename = config.get('PICKLE_FILENAME')
    pickle.dump(searches, open(filename, 'wb'))

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/searches', methods=['GET'])
def get_searches():
    searches = load_searches()
    return jsonify(list(searches.values()))

@app.route('/searches/<string:query>', methods=['DELETE'])
def del_search(query):
    searches = load_searches()
    if not query in searches.keys():
        return jsonify({'error': 'Invalid search'}, 400)
    search_copy = searches[query].copy()
    del searches[query]
    dump_searches(searches)
    return jsonify(search_copy)

@app.route('/searches/<string:query>', methods=['PUT'])
def update_search(query):
    searches = load_searches()
    search = searches[query]
    if not search:
        print('no hay search')
        abort(400)
    if not request.json:
        print('no me llego la data en el json del request')
        abort(400)
    if query != request.json.get('query', None):
        abort(400)
    search['filters'] = request.json['filters']
    search['ids'] = request.json['ids']
    dump_search(search)
    return jsonify(search)

@app.route('/searches/<string:query>', methods=['GET'])
def get_search(query):
    searches = load_searches()
    try:
        return jsonify(searches[query])
    except KeyError:
        abort(404)

@app.route('/searches', methods=['POST'])
def add_search():
    if not request.json or not 'query' in request.json:
        abort(400)
    search = {
        'query': request.json['query'],
        'filters': request.json.get('filters', []),
        'ids': request.json.get('ids', []),
    }
    dump_search(search)
    return jsonify(search), 201

if __name__ == '__main__':
    app.run(debug=True)


# TODO
