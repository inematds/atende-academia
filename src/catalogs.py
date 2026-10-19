"""Cadastros da equipe; alterações ficam no banco, não na semente."""
import datetime as dt
import re

from .domain import Error, require

DAYS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')
FIELDS = {
    'professores': {'nome': str, 'avaliacao': bool, 'ativo': bool},
    'grade': {'modalidade': str, 'professor': str, 'sala': str, 'dia': str,
              'hora': str, 'duracao_min': int, 'vagas': int, 'ativo': bool},
    'modalidades': {'nome': str}, 'salas': {'nome': str},
    'faq': {'perguntas': list, 'resposta': str},
}


def clock(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}', value):
        raise Error(400, 'hora_invalida')
    return dt.time.fromisoformat(value)


def validate(app, collection, item):
    if collection == 'professores' and item['horarios'] is not None:
        windows = item['horarios']
        if not isinstance(windows, dict) or any(day not in DAYS for day in windows):
            raise Error(400, 'horarios_invalidos')
        for intervals in windows.values():
            if not isinstance(intervals, list):
                raise Error(400, 'horarios_invalidos')
            for pair in intervals:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise Error(400, 'horarios_invalidos')
                if clock(pair[0]) >= clock(pair[1]):
                    raise Error(422, 'intervalo_invalido')
    if collection == 'grade':
        if item['dia'] not in DAYS:
            raise Error(400, 'dia_invalido')
        clock(item['hora'])
        for field, target in (('modalidade', 'modalidades'), ('professor', 'professores'), ('sala', 'salas')):
            if app.store.get(target, item[field]) is None:
                raise Error(422, field + '_inexistente')
        if item['duracao_min'] <= 0 or item['vagas'] <= 0:
            raise Error(422, 'grade_invalida')
    if collection == 'faq':
        if any(not isinstance(q, str) or not q.strip() for q in item['perguntas']):
            raise Error(400, 'perguntas_invalidas')
        if not item['perguntas']:
            raise Error(422, 'perguntas_vazias')


def catalog(app, collection, identifier, method, body):
    store = app.store
    if method == 'GET' and identifier is None:
        return 200, {collection: store.all(collection)}
    if method == 'POST' and identifier is None:
        required = {k: t for k, t in FIELDS[collection].items() if k not in ('avaliacao', 'ativo')}
        if collection != 'faq':
            required['id'] = str
        require(body, required)
        if collection == 'faq':
            identifier = store.next_id('faq')
            while store.get(collection, identifier):
                identifier = store.next_id('faq')
        else:
            identifier = body['id']
            if not re.fullmatch(r'[\w-]+', identifier):
                raise Error(400, 'id_invalido')
        if store.get(collection, identifier):
            raise Error(409, 'id_duplicado')
        item = {'id': identifier}
        if collection in ('grade', 'professores'):
            item['ativo'] = True
        if collection == 'professores':
            item.update(avaliacao=False, horarios=None)
    elif identifier is not None and method in ('PUT', 'DELETE'):
        if collection in ('modalidades', 'salas') or (collection == 'faq' and method == 'PUT'):
            raise Error(404, 'rota_inexistente')
        item = app.get(collection, identifier)
        if method == 'DELETE':
            if collection == 'faq':
                store.delete(collection, identifier)
                return 204, None
            item['ativo'] = False
            store.save(collection, item)
            return 200, {'ativo': False}
    else:
        raise Error(404, 'rota_inexistente')
    require(body, {k: t for k, t in FIELDS[collection].items() if k in body})
    allowed = set(FIELDS[collection])
    if collection == 'professores':
        allowed.add('horarios')
    item.update({k: v for k, v in body.items() if k in allowed})
    validate(app, collection, item)
    store.save(collection, item)
    return (201 if method == 'POST' else 200), item
