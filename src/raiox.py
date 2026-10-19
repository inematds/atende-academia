"""Indicadores mensais e atualização do acompanhamento local do Raio-X."""
import calendar
import datetime as dt
import json
from pathlib import Path

from .classes import ACTIVE, Classes


def report(app, month):
    first = dt.date.fromisoformat(month + '-01')
    last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
    store = app.store
    enrollments = store.all('matriculas')
    valid = [x for x in enrollments if x['situacao'] != 'cancelada']
    active = {x['aluno_id'] for x in valid if x['situacao'] == 'ativa' and x['inicio'] <= last.isoformat() <= x['fim']}
    checkins = sum(x['quando'][:7] == month for x in store.all('checkins'))
    reservations = [x for x in store.all('reservas') if x['data'][:7] == month]
    marked = [x for x in reservations if x['status'] in ('presente', 'falta')]
    capacity = sum(x['vagas'] for x in Classes(app).occurrences({'de': [first.isoformat()], 'ate': [last.isoformat()]}) if not x['cancelada'])
    initial = {}
    for enrollment in enrollments:
        aid = enrollment['aluno_id']
        initial[aid] = min(initial.get(aid, enrollment['inicio']), enrollment['inicio'])
    ending = [x for x in valid if x['fim'][:7] == month]
    renewed = 0
    for enrollment in ending:
        end = dt.date.fromisoformat(enrollment['fim'])
        renewed += any(x['aluno_id'] == enrollment['aluno_id'] and x['id'] != enrollment['id']
                       and abs((dt.date.fromisoformat(x['inicio']) - end).days) <= 30 for x in valid)
    def ratio(numerator, denominator, scale=100):
        return round(numerator / denominator * scale, 1) if denominator else 0
    return {'pacote': 'servicos', 'mes': month, 'valores': {
        'atendimentos_mes': checkins,
        'falta_pct': ratio(sum(x['status'] == 'falta' for x in marked), len(marked)),
        'ocupacao_pct': ratio(sum(x['status'] in ACTIVE for x in reservations), capacity),
        'clientes_novos_mes': sum(value[:7] == month for value in initial.values()),
        'retorno_atual_pct': ratio(renewed, len(ending)),
        'atendimentos_mes_recorrente': ratio(checkins, len(active), 1),
    }, 'indicadores': {'alunos_ativos': len(active),
                      'cancelamentos_mes': sum(x.get('cancelada_em', '')[:7] == month for x in enrollments)}}


def update(app, month, filename):
    path = Path(filename)
    data = json.loads(path.read_text(encoding='utf-8'))
    previous = [x for x in data['meses'] if x['mes'] < month]
    baseline = max(previous, key=lambda x: x['mes']) if previous else data['base']
    values = dict(baseline['valores'])
    values.update(report(app, month)['valores'])
    data['meses'] = sorted([x for x in data['meses'] if x['mes'] != month] +
                           [dict(mes=month, valores=values, obs='atende-academia')], key=lambda x: x['mes'])
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
